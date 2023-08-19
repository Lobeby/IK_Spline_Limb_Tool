'''----------------------------------------------------
IK Spline Limb Tool  |  v.11 global clean up
----------------------------------------------------'''

### Usage example to run in Maya

'''
from importlib import reload
import IKspline_Limb_Tool
reload( IKspline_Limb_Tool )

limb_type = cmds.confirmDialog( title = 'Limb Type', message = 'Select the limb type:', button = ['Arm', 'Leg'] )
    
# Example values for the number of skinning joints : Modify these values as needed
num_SKIN_jnts_up = 5
num_SKIN_jnts_low = 5
# Change the radius of the control joints
jnt_radius = 2 

IKspline_Limb_Tool.create_bendy_limb( limb_type, num_SKIN_jnts_up, num_SKIN_jnts_low, jnt_radius )
'''

import maya.cmds as cmds
import maya.OpenMaya as om

### HELPERS

def float_range( start, stop, step ):
    return [ start + i * step for i in range( int( stop / step ) + 1 ) ]

def setZero( target ):
    attrs = [ '.translateX', '.translateY', '.translateZ', '.rotateX', '.rotateY', '.rotateZ', '.scaleX', '.scaleY', '.scaleZ' ]
    for attr in attrs:
        cmds.setAttr( target + attr, 0 if 'scale' not in attr else 1 )

def select_fk_joints( ):
    try:
        selected_joints = cmds.ls( sl = True )
        if len( selected_joints ) != 3:
            raise ValueError( "// Please select exactly 3 FK joints of the Limb. //" )
        return selected_joints
    except:
        raise ValueError( "// Please select all the 3 FK joints of the Limb. //" )

### SETUPS

def create_bend_control_joints( start_jnt, prefix, jnt_radius, root_jnt_grp, tip_jnt_grp, system_grp, do_not_touch ):

    '''
    Creates the bend_jnt that drives the IK Spline 
    and constraint it to the existing FK joints
    '''
    
    bend_jnt = cmds.duplicate( start_jnt, name = prefix + '_Bend_CTRL_JNT', po = 1 )[0]
    cmds.setAttr( bend_jnt + '.radius', jnt_radius )
    cmds.makeIdentity( bend_jnt, apply = True, scale = True )
    bend_jnt_grp = cmds.group( name = str( bend_jnt ) + '_OFFSET', em = 1 )

    cmds.pointConstraint( root_jnt_grp, tip_jnt_grp, bend_jnt_grp, name = bend_jnt + '_parCstr', mo = 0 )
    aim_up_LOC = cmds.createNode( 'locator', name = bend_jnt + '_aim_up_LOCShape' )
    aim_up_LOC = cmds.listRelatives( aim_up_LOC, p = 1 )[0]
    cmds.rename( aim_up_LOC, bend_jnt + '_aim_up_LOC' )
    cmds.parent( aim_up_LOC, do_not_touch )
    cmds.pointConstraint( root_jnt_grp, tip_jnt_grp, aim_up_LOC, mo = 0, name = aim_up_LOC + '_pntCstr' )
    cmds.orientConstraint( root_jnt_grp, tip_jnt_grp, aim_up_LOC, mo = 0, name = aim_up_LOC + '_ori_cstr' )
    cmds.setAttr( aim_up_LOC + '_ori_cstr.interpType', 2 ) # ( with Shortest parameter )
    cmds.aimConstraint( tip_jnt_grp, bend_jnt_grp, 
        aimVector = ( 0, 1, 0 ), 
        upVector = ( 1, 0, 0 ), 
        worldUpType = "objectrotation", 
        worldUpVector = ( 1, 0, 0 ), 
        worldUpObject = aim_up_LOC, 
        name = bend_jnt + '_aimCstr', mo = 0 )

    cmds.parent( bend_jnt, bend_jnt_grp )
    setZero( bend_jnt )
    cmds.makeIdentity( bend_jnt, apply = True, scale = True )
    cmds.parent( bend_jnt_grp, system_grp )
    bend_jnt_CTRL, __ = cmds.circle( name = bend_jnt + '_CTRL', nr = ( 0, 1, 0 ), r = 7 )
    cmds.delete( __ )
    cmds.parent( bend_jnt_CTRL, bend_jnt_grp )
    setZero( bend_jnt_CTRL )
    cmds.makeIdentity( bend_jnt_CTRL, apply = True, scale = True )

    cmds.parent( bend_jnt, bend_jnt_CTRL )

    return bend_jnt

def create_SKIN_joints( num_SKIN_jnts, trans_y, root_jnt, prefix, jnt_radius, system_grp, tip_jnt ):

    '''
    Creates the skinning joints 
    '''

    nb_jnts = int( num_SKIN_jnts ) 
    trans_y_jnts = trans_y / nb_jnts

    limb_01_SKIN = cmds.duplicate( root_jnt, name = prefix + '_01_SKIN', po = 1 )[0]
    cmds.setAttr( limb_01_SKIN + '.radius', jnt_radius/2 )
    cmds.makeIdentity( limb_01_SKIN, apply = True, scale = True )

    cmds.parent( limb_01_SKIN, system_grp )

    limb_SKIN_jnts = [ limb_01_SKIN ]

    for i in range( nb_jnts ):
        limb_SKIN = cmds.duplicate( limb_01_SKIN, name = prefix + '_0' + str( i + 2 ) + '_SKIN', po = 1 )[0]
        cmds.parent( limb_SKIN, limb_SKIN_jnts[-1] )
        cmds.setAttr( limb_SKIN + '.translateY', trans_y_jnts )
        limb_SKIN_jnts.append( limb_SKIN )
    
    cmds.matchTransform( limb_SKIN_jnts[-1], tip_jnt, pos = 1, rot = 0, scl = 0 )

    limb_SKIN_jnts[0] = cmds.rename( limb_SKIN_jnts[0], prefix + '_01_notSKIN' )
    limb_SKIN_jnts[-1] = cmds.rename( limb_SKIN_jnts[-1], prefix + '_tip_notSKIN' )

    return limb_SKIN_jnts, nb_jnts, trans_y_jnts

def create_ik_spline( prefix, limb_SKIN_jnts, do_not_touch, root_jnt, bend_jnt, tip_jnt, trans_y ):

    '''
    Creates the IK Spline on the skinning joints,
    skin the curve to the Root, Bend and Tip joints
    and set the advanced twist controls 
    '''

    limb_ik_hdl, limb_eff, limb_crv = cmds.ikHandle( name = prefix + "_IK_HDL", sol = 'ikSplineSolver', sj = limb_SKIN_jnts[0], ee = limb_SKIN_jnts[-1] )
    limb_crv = cmds.rename( limb_crv, prefix + "_crv" )
    limb_eff = cmds.rename( limb_eff, prefix + "_eff" )
    cmds.parent( limb_eff, limb_SKIN_jnts[-1] )
    cmds.parent( limb_crv, limb_ik_hdl, do_not_touch )
    cmds.select( root_jnt, bend_jnt, tip_jnt, limb_crv )
    cmds.skinCluster( name = limb_crv + '_SKINCluster' )

    if abs( trans_y ) == trans_y:
        attr = [ 2, 6, 1 ]
    else:
        attr = [ 3, 7, -1 ]

    cmds.setAttr( limb_ik_hdl + '.dTwistControlEnable', 1 )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpType', 4 )
    cmds.setAttr( limb_ik_hdl + '.dForwardAxis', attr[0] )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpAxis', attr[1] )

    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorX', attr[2] )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorY', 0 )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorZ', 0 )

    cmds.connectAttr( root_jnt + '.worldMatrix[0]', limb_ik_hdl + '.dWorldUpMatrix', f = 1 )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorEndX', attr[2] )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorEndY', 0 )
    cmds.setAttr( limb_ik_hdl + '.dWorldUpVectorEndZ', 0 )
    cmds.connectAttr( tip_jnt + '.worldMatrix[0]', limb_ik_hdl + '.dWorldUpMatrixEnd', f = 1 )

    return limb_crv

def create_squash_and_stretch( nb_jnts, prefix, limb_crv, trans_y, limb_SKIN_jnts, start_jnt ):

    '''
    Creates the stretch with pointOnCurveInfo and distanceBetween node connections
    and the squash with multiplyDivide nodes ( Global Scale ) with the value of scale from the joints
    '''

    # pointOnCurveInfo Nodes

    poci_nodes = []
    range_step = 1/( nb_jnts ) # 0.25 = 1/( 5-1 ) et 5 = number of joints that you create total for in between
    param = float_range( 0, 1, range_step )
    for i in range( nb_jnts + 1 ):   
        poci = cmds.createNode( 'pointOnCurveInfo', name = prefix + '_poci_0' + str( i + 1 ) )
        poci_nodes.append( poci )
        cmds.connectAttr( limb_crv + 'Shape.worldSpace', poci + '.inputCurve', f = 1 )
        cmds.setAttr( poci + '.turnOnPercentage', 1 )
        cmds.setAttr( poci + '.parameter', param[i] )
        cmds.setAttr( poci + '.parameter', k = 1 )

    # distanceBetween AND MultiplyDivide ( Global Scale ) Nodes

    dist_btw_nodes = []
    for i in range( nb_jnts ): 
        dist_btw = cmds.createNode( 'distanceBetween', name = prefix + '_dist_btw_0' + str( i + 1 ) )
        dist_btw_nodes.append( dist_btw )
        cmds.connectAttr( poci_nodes[int( i )] + '.position', dist_btw + '.point1', f = 1 )
        cmds.connectAttr( poci_nodes[int( i + 1 )] + '.position', dist_btw + '.point2', f = 1 )
        mult_div = cmds.createNode( 'multiplyDivide', name = prefix + '_globalScale_0' + str( i + 1 ) )
        cmds.setAttr( mult_div + '.operation', 2 )
        cmds.connectAttr( dist_btw + '.distance', mult_div + '.input1X', f = 1 )

        if abs( trans_y ) == trans_y:
            cmds.connectAttr( 'main_CTRL.scaleY', mult_div + '.input2X', f = 1 )
        else:
            mult_dbl_lin = cmds.createNode( 'multDoubleLinear', name = prefix + '_inversemult_dbl_lin_0' + str( i + 1 ) )
            cmds.setAttr( mult_dbl_lin + '.input2', -1 )
            cmds.connectAttr( 'main_CTRL.scaleY', mult_dbl_lin + '.input1', f = 1 )
            cmds.connectAttr( mult_dbl_lin + '.output', mult_div + '.input2X', f = 1 )
        
        cmds.connectAttr( mult_div + '.outputX', limb_SKIN_jnts[int( i + 1 )] + '.translateY', f = 1 )

    # squash on the SKIN jnts with the value of scale from selected joints

    stretch_condition = cmds.listConnections( start_jnt, s = 1, type = 'condition' )[0]
    vc_pow = cmds.createNode( 'multiplyDivide', name = prefix + '_volumicConservation_pow' )
    cmds.connectAttr( stretch_condition + '.outColorR', vc_pow + '.input1X', f = 1 )
    cmds.setAttr( vc_pow + '.operation', 3 )
    cmds.setAttr( vc_pow + '.input2X', 0.5 )
    vc_invert = cmds.createNode( 'multiplyDivide', name = prefix + '_volumicConservation_invert' )
    cmds.connectAttr( vc_pow + '.outputX', vc_invert + '.input2X', f = 1 )
    cmds.setAttr( vc_invert + '.operation', 2 )
    cmds.setAttr( vc_invert + '.input1X', 1 )

    # connect the result of each limb_SKIN_jnts jnt scale X and Z

    for i in range( nb_jnts ):
        cmds.connectAttr( vc_invert + '.outputX', limb_SKIN_jnts[int( i )] + '.scaleX', f = 1 )
        cmds.connectAttr( vc_invert + '.outputX', limb_SKIN_jnts[int( i )] + '.scaleZ', f = 1 )

def refine_curve( limb_crv ):

    cmds.setAttr( limb_crv + '.inheritsTransform', 0 )
    cmds.rebuildCurve( limb_crv, kcp = 1, d = 2, name = limb_crv + '_rebuildCrv' )
    cmds.setAttr( limb_crv + '.spans', 8 )

def create_half_bone( position, joint, previous_jnt, side_name, half_bone_name, jnt_radius, trans_y, trans_y_jnts, upper_jnt_grp , lower_jnt_grp ):

    half_bone = cmds.duplicate( joint, name = side_name + half_bone_name + '_HalfBone', po = 1 )[0]
    half_bone_grp = cmds.group( name = str( half_bone ) + '_OFFSET', em = 1 )
    cmds.setAttr( half_bone + '.radius', jnt_radius*2 )
    cmds.makeIdentity( half_bone, apply = True, scale = True )
    cmds.matchTransform( half_bone_grp, half_bone, scl = 0 )
    cmds.parent( half_bone, half_bone_grp )
    cmds.pointConstraint( joint, half_bone, name = half_bone + '_pntCstr', mo = 0 )
    ori_cstr = cmds.orientConstraint( previous_jnt, joint, half_bone, name = half_bone + '_ori_cstr', mo = 1 )[0]
    cmds.setAttr( ori_cstr + '.interpType', 2 ) # ( with Shortest parameter )

    if position == 'mid':
        half_bone_CTRL, __ = cmds.circle( name = half_bone + '_CTRL', nr = ( 0, 1, 0 ), r = 10 )
        cmds.delete( __ )
        cmds.parent( half_bone_CTRL, half_bone )
        setZero( half_bone_CTRL )
        cmds.makeIdentity( half_bone_CTRL, apply = True, scale = True )
        cmds.parent( upper_jnt_grp, half_bone_CTRL ) # parent upper_limb_tip_jnt_grp under the halfbone
        cmds.parent( lower_jnt_grp, half_bone_CTRL ) # parent lower_limb_root_jnt_grp under the halfbone
        half_bone = half_bone_CTRL

    if position == 'root':
        cmds.parent( upper_jnt_grp, half_bone ) # parent upper_limb_root_jnt_grp under the halfbone


    half_bone_SKIN = cmds.duplicate( half_bone, name = side_name + half_bone_name + '_HalfBone_SKIN', po = 1 )[0]
    cmds.setAttr( half_bone_SKIN + '.radius', jnt_radius/2 )
    cmds.parent( half_bone_SKIN, half_bone )

    if position == 'tip':
        aim_LOC = cmds.createNode( 'locator', name = half_bone_SKIN + '_aim_LOCShape' )
        aim_LOC = cmds.listRelatives( aim_LOC, p = 1 )[0]
        cmds.rename( aim_LOC, half_bone_SKIN + '_aim_LOC' )
        cmds.parent( aim_LOC, half_bone )
        setZero( aim_LOC )
        cmds.setAttr( aim_LOC + '.translateY', trans_y_jnts )
        cmds.makeIdentity( aim_LOC, apply = True, scale = True )
        
        if abs( trans_y ) == trans_y:
            main_axis = 1
        else:
            main_axis = -1
        cmds.aimConstraint( aim_LOC, half_bone_SKIN, 
            aimVector = ( 0, main_axis, 0 ), 
            upVector = ( 1, 0, 0 ), 
            worldUpType = "objectrotation", 
            worldUpVector = ( 1, 0, 0 ), 
            worldUpObject = joint, 
            name = half_bone_SKIN + '_aimCstr', mo = 0 )

        cmds.parent( lower_limb_tip_jnt_grp, half_bone_SKIN )

    return half_bone_grp

### MAIN CODE

def create_bendy_limb( limb_type, num_SKIN_jnts_up, num_SKIN_jnts_low, jnt_radius ):

    if limb_type == 'Arm':
        half_bone_name = ['shoulder', 'elbow', 'wrist']
    elif limb_type == 'Leg':
        half_bone_name = ['hip', 'knee', 'ankle']
    else:
        cmds.warning( '// Invalid limb type. Use "Arm" or "Leg". //' )
        return

    start_jnt, mid_jnt, end_jnt = select_fk_joints( )[:3]
    side_name = start_jnt.split( '_' )[0] + '_'

    for jnt in [ start_jnt, mid_jnt, end_jnt ]:
        if not cmds.objectType( jnt, isType = 'joint' ):
            cmds.warning( 'Please select joints of the limb.' )
            return

    num_SKIN_jnts = [ num_SKIN_jnts_up, num_SKIN_jnts_low ]

    # Creating system group hierarchy

    upper_system_grp = cmds.group( name = side_name + 'upper' + limb_type + '_system', em = 1 )
    cmds.matchTransform( upper_system_grp, start_jnt, pos = 1, rot = 1, scl = 0 )
    cmds.makeIdentity( upper_system_grp, apply = True, scale = True ) # je freeze scale upper_system_grp parce que ça crée des transform autrement...

    lower_system_grp = cmds.group( name = side_name + 'lower' + limb_type + '_system', em = 1 )
    cmds.matchTransform( lower_system_grp, mid_jnt, pos = 1, rot = 1, scl = 0 )
    cmds.makeIdentity( lower_system_grp, apply = True, scale = True ) # je freeze scale lower_system_grp parce que ça crée des transform autrement...

    system_grps = [ upper_system_grp, lower_system_grp ]
    do_not_touch = cmds.group( name = side_name + limb_type + '_do_not_touch', em = 1 )

    upperlimb_root_jnt = cmds.duplicate( start_jnt, name = side_name + 'upper' + limb_type + '_Root_CTRL_JNT', po = 1 )[0]
    upper_limb_root_jnt_grp = cmds.group( name = str( upperlimb_root_jnt ) + '_OFFSET', em = 1 )
    upperlimb_tip_jnt = cmds.duplicate( mid_jnt, name = side_name + 'upper' + limb_type + '_Tip_CTRL_JNT', po = 1 )[0]
    upper_limb_tip_jnt_grp = cmds.group( name = str( upperlimb_tip_jnt ) + '_OFFSET', em = 1 )

    lower_limb_root_jnt = cmds.duplicate( mid_jnt, name = side_name + 'lower' + limb_type + '_Root_CTRL_JNT', po = 1 )[0]
    lower_limb_root_jnt_grp = cmds.group( name = str( lower_limb_root_jnt ) + '_OFFSET', em = 1 )
    lower_limb_tip_jnt = cmds.duplicate( end_jnt, name = side_name + 'lower' + limb_type + '_Tip_CTRL_JNT', po = 1 )[0]
    lower_limb_tip_jnt_grp = cmds.group( name = str( lower_limb_tip_jnt ) + '_OFFSET', em = 1 )

    limb_jnts = [ upperlimb_root_jnt, upperlimb_tip_jnt, lower_limb_root_jnt, lower_limb_tip_jnt ]
    limb_jnts_grp = [ upper_limb_root_jnt_grp, upper_limb_tip_jnt_grp, lower_limb_root_jnt_grp, lower_limb_tip_jnt_grp ]

    for i, limb_JNT in enumerate( limb_jnts ):

        cmds.makeIdentity( limb_JNT, apply = True, scale = True )
        cmds.setAttr( limb_JNT + '.radius', jnt_radius )
        cmds.matchTransform( limb_jnts_grp[i], limb_JNT, scl = 0 )
        cmds.makeIdentity( limb_jnts_grp[i], apply = True, scale = True )
        cmds.parent( limb_JNT, limb_jnts_grp[i] )

        if i < 2:
            cmds.parent( limb_jnts_grp[i], upper_system_grp )
        else:
            cmds.parent( limb_jnts_grp[i], lower_system_grp )

    limb_root_jnt = [ upperlimb_root_jnt, lower_limb_root_jnt ]
    limb_tip_jnt = [ upperlimb_tip_jnt, lower_limb_tip_jnt ]
    limb_root_jnt_grp = [ upper_limb_root_jnt_grp, lower_limb_root_jnt_grp ]
    limb_tip_jnt_grp = [ upper_limb_tip_jnt_grp, lower_limb_tip_jnt_grp ]

    trans_y_jnt = [ mid_jnt, end_jnt ]

    # Creating the upper and lower systems

    for x, uplo in enumerate( ['upper', 'lower'] ):

        root_jnt = limb_root_jnt[x]
        tip_jnt = limb_tip_jnt[x]
        root_jnt_grp = limb_root_jnt_grp[x]
        tip_jnt_grp = limb_tip_jnt_grp[x]

        trans_y = cmds.getAttr( trans_y_jnt[x] + '.translateY' )
        prefix = side_name + uplo + limb_type

        bend_jnt = create_bend_control_joints( start_jnt, prefix, jnt_radius, root_jnt_grp, tip_jnt_grp, system_grps[x], do_not_touch )
        limb_SKIN_jnts, nb_jnts, trans_y_jnts = create_SKIN_joints( num_SKIN_jnts[x], trans_y, root_jnt, prefix, jnt_radius, system_grps[x], tip_jnt )
        
        limb_crv = create_ik_spline( prefix, limb_SKIN_jnts, do_not_touch, root_jnt, bend_jnt, tip_jnt, trans_y )
        
        create_squash_and_stretch( nb_jnts, prefix, limb_crv, trans_y, limb_SKIN_jnts, start_jnt )
        
        refine_curve( limb_crv )

    # Creates the mid HalfBone joint ( elbow or knee ) and constrains it to the upper and lower systems
    mid_half_bone_grp = create_half_bone( 'mid', mid_jnt, start_jnt, side_name, half_bone_name[1], jnt_radius, trans_y, trans_y_jnts, upper_limb_tip_jnt_grp , lower_limb_root_jnt_grp )

    # Creates the root HalfBone joint ( shoulder or hip ) and constrains it to the existing FK joint and upper system
    root_half_bone_grp = create_half_bone( 'root', start_jnt, cmds.listRelatives( start_jnt , p = 1 ) [0], side_name, half_bone_name[0], jnt_radius, trans_y, trans_y_jnts, upper_limb_root_jnt_grp  )

    # Creates the tip HalfBone joint ( wrist or ankle ) and constrains it to the lower system and the existing FK joint 
    tip_half_bone_grp = create_half_bone( 'tip', end_jnt, mid_jnt, side_name, half_bone_name[2], jnt_radius, trans_y, trans_y_jnts, trans_y, trans_y_jnts )
    
    #  Final Offset Organisation

    ik_spline_limb_grp = cmds.group( name = side_name + limb_type + '_IkSpline_limb_OFFSET', em = 1 )
    cmds.parent( upper_system_grp, 
                lower_system_grp, 
                root_half_bone_grp, 
                mid_half_bone_grp, 
                tip_half_bone_grp, 
                do_not_touch, 
                ik_spline_limb_grp )

    # Rename the transformX nodes

    children = cmds.listRelatives( ik_spline_limb_grp, ad = 1 )
    for child in children:
        if child.startswith( 'transform' ):
            __, new_name = child.split( 'transform' )
            new_name = side_name + limb_type + '_Auto_Transform_Node_When_Reparenting_0' + new_name
            cmds.rename( child, new_name )

    om.MGlobal.displayInfo( '// Result: ' + side_name + limb_type + '_IkSpline_Limb created // ' )