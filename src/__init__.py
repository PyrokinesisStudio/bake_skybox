import bpy
from . import common

from asyncore import poll


bl_info = {
    "name" : "Bake render to Skybox",
    "author" : "Uiler",
    "version" : (0,1), 
    "blender" : (2, 7, 8),
    "location" : "User",
    "description" : "Bake rendering to skybox object.",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "User"
}

#########################################################
# Constants
#########################################################
_STAT_NONE = "NONE"
_STAT_START = "START"
_STAT_SAVING = "SAVING"
_STAT_END = "END"


#########################################################
# Global Variables
#########################################################
#########################################################
# Class
#########################################################
#########################################################
# Properties
#########################################################
class BakeRenderToSkyboxProperties(bpy.types.PropertyGroup):

    # System setting properties    
    bake_start = bpy.props.IntProperty(name="bake_start", description="Starting frame of range of baking to Skybox.", default=0, step=1, subtype='NONE')
    bake_end = bpy.props.IntProperty(name="bake_end", description="End frame of range of baking to Skybox.", default=250, step=1, subtype='NONE')
    
    output_dir = bpy.props.StringProperty(name="output_dir", description="output directly of skybox.", default="//output\\", subtype='DIR_PATH')
    output_prefix = bpy.props.StringProperty(name="output_prefix", description="prefix of output files.", default="skybox_", subtype="NONE")
    output_padding = bpy.props.IntProperty(name="output_padding", description="padding number of sequential number of output files", default=4, step=1, subtype='NONE')
    
def _defProperties():

    # Define Addon's Properties
    bpy.types.WindowManager.uil_bake_render_to_skybox_propgrp = bpy.props.PointerProperty(type=BakeRenderToSkyboxProperties)
    
#########################################################
# Functions(Private)
#########################################################
#########################################################
# Actions
#########################################################

class PickBakeRenderToSkyboxRangeStartFromCurrent(bpy.types.Operator):
    bl_idname = "uiler.pickbakerendertoskyboxrangestartfromcurrent"
    bl_label = "label"

    def execute(self, context):
        
        propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
        propgrp.bake_start = context.scene.frame_current

        return {'FINISHED'}

class PickBakeRenderToSkyboxRangeEndFromCurrent(bpy.types.Operator):
    bl_idname = "uiler.pickbakerendertoskyboxrangeendfromcurrent"
    bl_label = "label"

    def execute(self, context):
        
        propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
        propgrp.bake_end = context.scene.frame_current

        return {'FINISHED'}

class PickBakeRenderToSkyboxStartAndEndFromSceneStartAndEnd(bpy.types.Operator):
    bl_idname = "uiler.pickbakerendertoskyboxrangestartandend"
    bl_label = "label"

    def execute(self, context):
        
        propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
        propgrp.bake_start = context.scene.frame_start
        propgrp.bake_end = context.scene.frame_end

        return {'FINISHED'}

########################
# Bake To SkyBox
#
class BakeRenderToSkyBox(bpy.types.Operator):
    bl_idname = "uiler.bakerendertoskybox"
    bl_label = "Bake Render To Skybox"
#     bl_options = {'REGISTER', 'UNDO'}
    
    fcurr_bkup = bpy.props.IntProperty(default=2**31-1)
    _image = None
    _save_stat = _STAT_NONE

    def modal(self, context, event):

        wm = context.window_manager
        propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
        scene = context.scene

        b_start = propgrp.bake_start
        b_end = propgrp.bake_end

        if event.type == 'TIMER':

            fcurr = scene.frame_current
        
            if b_start <= fcurr <= b_end:
                print(scene.frame_current)

                if not self._image.is_dirty and self._save_stat != _STAT_START:
                    bpy.ops.object.bake(type='ENVIRONMENT')
                    self._save_stat = _STAT_START
                
                if self._image.is_dirty and self._save_stat != _STAT_SAVING:
                    self._save_stat = _STAT_SAVING
                    dir = bpy.path.abspath(propgrp.output_dir)
                    prefix = propgrp.output_prefix
                    padnum = propgrp.output_padding
                    seq = common.getPaddingStringByDigit(fcurr, padnum)
                    # ToDo Select Saving Image format
                    output_path = dir + prefix + seq + ".png"
                    self._save_stat = self._image.save_render(output_path)
                
                if not self._save_stat:
                    self._image.reload()
                    self._save_stat = _STAT_END
                
                if self._save_stat == _STAT_END:
                    scene.frame_current = fcurr + 1
                    self._save_stat = _STAT_NONE
                    wm.progress_update(fcurr - b_start)

            else:
                self._finish(context)
                return {'FINISHED'}


            return {'RUNNING_MODAL'}
        
        elif event.type in {'ESC'}:  # Cancel
            self._finish(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
        
    def invoke(self, context, event):
    
        propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
        scene = context.scene

        b_start = propgrp.bake_start
        b_end = propgrp.bake_end

        self.fcurr_bkup = scene.frame_current
        scene.frame_current = b_start
            
        wm = context.window_manager
        # timer start
        self._timer = wm.event_timer_add(time_step=0.1, window=context.window)
        wm.modal_handler_add(self)
        # Begin progress
        wm.progress_begin(0, b_end - b_start)
        
        # ToDo 
        self._image = bpy.data.images['output']
        
        
        return {'RUNNING_MODAL'}
    
    def _finish(self, context):
        
        print("finished!!!")

        context.scene.frame_current = self.fcurr_bkup
        self._image.reload()
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        wm.progress_end()


def draw_item(self, context):

    propgrp = context.window_manager.uil_bake_render_to_skybox_propgrp
    
    layout = self.layout
    box = layout.box()
    box.label(text="Render to Skybox")
    row = box.row()
    
    row.operator("uiler.bakerendertoskybox", text="Bake to Skybox", icon="RENDER_ANIMATION")

    row = box.row(align=True)
    row.operator("uiler.pickbakerendertoskyboxrangestartfromcurrent", text="", icon="TIME")
    row.prop(propgrp, "bake_start", text="Start")
    row.prop(propgrp, "bake_end", text="End")
    row.operator("uiler.pickbakerendertoskyboxrangeendfromcurrent", text="", icon="TIME")
    row.operator("uiler.pickbakerendertoskyboxrangestartandend", text="", icon="FILE_REFRESH")

    row = box.row(align=True)
    col = row.column(align=True)
    row = col.row(align=True)
    row.prop(propgrp, "output_dir", text="")
    row = col.row(align=True)
    row.prop(propgrp, "output_prefix", text="")
    row.prop(propgrp, "output_padding", text="padding:")
    
        

def register():
    bpy.utils.register_class(BakeRenderToSkyboxProperties)
    _defProperties()
    bpy.utils.register_module(__name__)

    bpy.types.CyclesRender_PT_bake.append(draw_item)

def unregister():
    bpy.utils.unregister_class(BakeRenderToSkyboxProperties)
    bpy.utils.unregister_module(__name__)

    bpy.types.CyclesRender_PT_bake.remove(draw_item)


if __name__ == "__main__":
    register()


