"""Build relief columns of the 3D periodic table from the SVGs in ./svg.

Run:  blender --background --python build.py     (saves periodic.blend)
  or: open in Blender's text editor and run there.
One Blender unit = 1 mm (the SVG importer maps these mm-sized files 1:1).
"""

import bmesh
import bpy
from math import radians
from mathutils import Matrix
from pathlib import Path

HERE = Path(bpy.data.filepath).parent if bpy.data.filepath else Path(__file__).parent
SVG_DIR = HERE / "svg"

BASE = 2.0  # thickness of the solid square
RELIEF = 0.8  # height of frame and text above the base
OVERLAP = 0.2  # how deep the relief sinks into the base
CELL = 20.0
GAP = 0.0  # between columns in the layout
MERGE = 1e-4  # vertices closer than this are welded
COLLINEAR = radians(0.5)  # outline points straighter than this are dropped


def import_svg(path):
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]


def select(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def is_collinear(vert):
    if len(vert.link_edges) != 2:
        return False
    a, b = (edge.other_vert(vert).co - vert.co for edge in vert.link_edges)
    return a.angle(b, 0) > radians(180) - COLLINEAR


def fill_outline(obj, z):
    # Blender's own curve fill leaves duplicate points and zero-area triangles, on which solidify builds crooked walls.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(Matrix.Translation((0, 0, z)) @ obj.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=MERGE)
    bmesh.ops.dissolve_verts(bm, verts=[vert for vert in bm.verts if is_collinear(vert)])
    bmesh.ops.triangle_fill(bm, use_dissolve=True,edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.matrix_world = Matrix.Identity(4)


def solidify(obj, bottom, top):
    obj.data.dimensions = "2D"
    obj.data.fill_mode = "NONE"
    select([obj])
    bpy.ops.object.convert(target="MESH")
    fill_outline(obj, (bottom + top) / 2)
    modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
    modifier.thickness = top - bottom
    modifier.offset = 0
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def join(objects, name):
    select(objects)
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = result.data.name = name
    return result


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def move_to_scene_collection(obj):
    for collection in obj.users_collection:
        collection.objects.unlink(obj)
        if collection != bpy.context.scene.collection and not collection.all_objects:
            bpy.data.collections.remove(collection)
    bpy.context.scene.collection.objects.link(obj)


def build_column(frame_path, index):
    name = frame_path.name.removesuffix("-frame.svg")
    old_materials = set(bpy.data.materials)
    frames = import_svg(frame_path)
    reliefs = import_svg(frame_path.with_name(f"{name}-text.svg"))
    for obj in frames:
        solidify(obj, 0, BASE)
    for obj in reliefs:
        solidify(obj, BASE - OVERLAP, BASE + RELIEF)
    column = join(frames + reliefs, name)
    fix_normals(column)
    # the importer creates one material per path
    column.data.materials.clear()
    for material in set(bpy.data.materials) - old_materials:
        bpy.data.materials.remove(material)
    move_to_scene_collection(column)
    for collection in list(bpy.data.collections):
        if not collection.all_objects:
            bpy.data.collections.remove(collection)
    top = max(v.co.y for v in column.data.vertices)
    left = min(v.co.x for v in column.data.vertices)
    column.location = (index * (CELL + GAP) - left, -top, 0)
    return column


def main():
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 0.001
    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
    for index, frame_path in enumerate(sorted(SVG_DIR.glob("*-frame.svg"))):
        build_column(frame_path, index)
    if bpy.app.background:
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "periodic.blend"))


main()
