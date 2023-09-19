# IK Spline Limb Tool

This tool is designed to automate the creation of an inverse kinematics (IK) Spline limb setup in Autodesk Maya. It generates a flexible limb rig with advanced controls for bending, stretching, and squashing. The tool supports both arm and leg types and streamlines the process of rigging character limbs. The script is suitable for use in animation and character rigging pipelines within Maya.

![Thumbnail_Custom_Github_upgrade](https://github.com/Lobeby/IK_Spline_Limb_Tool/assets/94933916/d59117e3-26ee-49ea-bbb3-a72e4e953fa5)

## Installation

To use the IK Spline Limb Tool, follow these steps:

1. Open the Autodesk Maya test scene.
2. Copy the provided Python script to a Python script editor within Maya.
3. Select the three joints and run the script.

After running the script, you can create IK Spline limbs using the provided functions. The script includes an example of how to use these functions to create a bendy limb. You can customize the limb type (arm or leg), the number of skinning joints, and the joint radius according to your requirements.

## Example Usage

```python
from importlib import reload
import IKspline_Limb_Tool
reload(IKspline_Limb_Tool)

limb_type = cmds.confirmDialog(
    title='Limb Type',
    message='Select the limb type:',
    button=['Arm', 'Leg']
)

# Example values for the number of skinning joints: Modify these values as needed
num_SKIN_jnts_up = 5
num_SKIN_jnts_low = 5
# Change the radius of the control joints
jnt_radius = 2

IKspline_Limb_Tool.create_bendy_limb(limb_type, num_SKIN_jnts_up, num_SKIN_jnts_low, jnt_radius)
```

## Features

- Automatically creates bendy IK Spline limbs for both arms and legs.
- Generates advanced control joints for better manipulation.
- Supports adjustable number of skinning joints and control joints size.
- Incorporates stretching and squashing functionality for natural deformations.
- Hierarchical organization of limb components for easy management.
- Provides informative feedback through the Maya interface.

## Important Notes

- This tool requires Autodesk Maya to run.
- The provided Python script contains comments explaining the various functions and their usage.
- Please note that this script is designed for a specific project and may require some modifications or adjustments to suit your specific needs and character rigs.

---

*Credits : This tool was created by Léa Béchard. For more information, contact lbechard@artfx.fr.*
