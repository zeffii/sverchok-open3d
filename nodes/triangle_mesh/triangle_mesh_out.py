
import numpy as np

import bpy
from bpy.props import  BoolVectorProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_mesh_utils import polygons_to_edges_np
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

import numpy as np
from sverchok_open3d.dependencies import open3d as o3d
from sverchok_open3d.utils.triangle_mesh import calc_normals, calc_centers
from sverchok.utils.dummy_nodes import add_dummy

if o3d is None:
    add_dummy('SvO3TriangleMeshOutNode', 'Triangle Mesh Out', 'open3d')
else:
    class SvO3TriangleMeshOutNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
        """
        Triggers: O3D Triangle Mesh Out
        Tooltip: O3D Triangle Mesh Out
        """
        bl_idname = 'SvO3TriangleMeshOutNode'
        bl_label = 'Triangle Mesh Out'
        bl_icon = 'MESH_DATA'
        # sv_icon = 'SV_RANDOM_NUM_GEN'

        default_np = (False for i in range(10))
        out_np: BoolVectorProperty(
            name="Ouput Numpy",
            description="Output NumPy arrays",
            # default=default_np,
            size=10, update=updateNode)
        def sv_init(self, context):
            self.inputs.new('SvO3TriangleMeshSocket', "O3D Triangle Mesh").is_mandatory = True

            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvVerticesSocket', "Vertex Normals")
            self.outputs.new('SvColorSocket', "Vertex Colors")
            self.outputs.new('SvVerticesSocket', "Face Normals")
            self.outputs.new('SvVerticesSocket', "Face Centers")
            self.outputs.new('SvVerticesSocket', "UV Verts")
            self.outputs.new('SvStringsSocket', "UV Faces")
            self.outputs.new('SvStringsSocket', "Material Id")



        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'list_match')
            layout.label(text="Ouput Numpy:")
            r = layout.column()
            for i in range(len(self.outputs)):
                r.prop(self, "out_np", index=i, text=self.outputs[i].name, toggle=True)
        def rclick_menu(self, context, layout):
            layout.prop_menu_enum(self, "list_match", text="List Match")
        def process_data(self, params):
            outputs = self.outputs

            mesh_s = params[0]
            vertices_out, verts_normals_out, verts_colors_out = [], [], []
            edges_out = []
            faces_out, f_normals_out, f_centers_out = [], [], []
            uv_verts_out, uv_faces_out, material_id_out = [], [], []

            for mesh in mesh_s:
                if outputs['Vertices'].is_linked:
                    vertices_out.append(np.asarray(mesh.vertices) if self.out_np[0] else np.asarray(mesh.vertices).tolist())

                if (outputs['Faces'].is_linked or outputs['Edges'].is_linked) and mesh.has_triangles():
                    tris = np.asarray(mesh.triangles)
                    if  outputs['Edges'].is_linked:
                        edges = polygons_to_edges_np([tris], unique_edges=True, output_numpy=self.out_np[1])[0]
                        edges_out.append(edges)
                    if  outputs['Faces'].is_linked:
                        faces_out.append(tris if self.out_np[2] else tris.tolist())
                else:
                    faces_out.append([])
                    edges_out.append([])

                if outputs['Vertex Normals'].is_linked and mesh.has_vertex_normals():
                    verts_normals_out.append(np.asarray(mesh.vertex_normals) if self.out_np[3] else np.asarray(mesh.vertex_normals).tolist())
                else:
                    verts_normals_out.append([])

                if outputs['Vertex Colors'].is_linked and mesh.has_vertex_colors():
                    colors = np.asarray(mesh.vertex_colors)
                    colors_a = np.ones((colors.shape[0], 4))
                    colors_a[:,:3] = colors
                    verts_colors_out.append(colors_a if self.out_np[4] else colors_a.tolist())
                else:
                    verts_colors_out.append([])


                if outputs['Face Normals'].is_linked:
                    if mesh.has_triangle_normals():
                        f_normals_out.append(np.asarray(mesh.triangle_normals) if self.out_np[5] else np.asarray(mesh.triangle_normals).tolist())
                    else:
                        f_normals_out.append(calc_normals(mesh, v_normals=False, output_numpy=self.out_np[5]))


                if outputs['Face Centers'].is_linked:
                    f_centers_out.append(calc_centers(mesh, output_numpy=self.out_np[6]))

                if mesh.has_triangle_uvs() and (outputs['UV Verts'].is_linked or outputs['UV Faces'].is_linked):
                    uvs = np.asarray(mesh.triangle_uvs)
                    new_uvs = np.zeros((uvs.shape[0],3), dtype='float')
                    new_uvs[:, :2] = uvs
                    uv_verts_out.append(new_uvs if self.out_np[7] else new_uvs.tolist())
                    uv_faces = np.arange(new_uvs.shape[0], dtype='int').reshape(-1,3)
                    uv_faces_out.append(uv_faces if self.out_np[8] else uv_faces.tolist())
                else:
                    uv_verts_out.append([])
                    uv_faces_out.append([])

                if mesh.has_triangle_material_ids() and self.outputs['Material Id'].is_linked:
                    material_id_out.append(np.asarray(mesh.triangle_material_ids) if self.out_np[9] else np.asarray(mesh.triangle_material_ids).tolist())
                else:
                    material_id_out.append([])


            return vertices_out, edges_out, faces_out, verts_normals_out, verts_colors_out, f_normals_out, f_centers_out, uv_verts_out, uv_faces_out, material_id_out




def register():
    if o3d is not None:
        bpy.utils.register_class(SvO3TriangleMeshOutNode)

def unregister():
    if o3d is not None:
        bpy.utils.unregister_class(SvO3TriangleMeshOutNode)
