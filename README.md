# Blender FLIP Fluids

**FLIP Fluids** is a powerful liquid simulation plugin that gives you the ability to create high quality fluid effects all within [Blender](https://www.blender.org/), the free and open source 3D creation suite. Created by Ryan Guy and Dennis Fassbaender.

## FLIP Fluids Beta

The core fluid engine, a FLIP-based fluid solver, has been under development for over three years with over a year of development focused on tightly integrating the simulator into Blender as an addon. We are excited to announce that the **FLIP Fluids simulator** is now ready to enter a beta testing phase! **The beta will begin on February 13th**.

<p align="center">
<a href="https://www.youtube.com/watch?v=5s7L3ruVaXk"><img src="http://rlguy.com/blender_flip_fluids/images/call_for_beta_testers_youtube.png" width="600px"></a>
</p>

Find out more about the **FLIP Fluids Beta** and how to request an invite here: [FLIP Fluids Beta Information](../../wiki/FLIP-Fluids-Beta-Information-and-Resources)

## Features

<table>
  <tr>
    <td width="50%" valign="top">
<h3>High Performance</h3>
The core fluid engine, written in C++, is designed for running high performance computations and massive physics calculations efficiently. Multithreaded and able to leverage the power of your GPU, this simulator is optimized for speed.
    </td>
    <td>
      <img src="http://rlguy.com/blender_flip_fluids/images/high_performance.jpg">
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="http://rlguy.com/blender_flip_fluids/images/whitewater_simulation.jpg">
    </td>
    <td valign="top">
<h3>Whitewater Generation</h3>
Create awesome large scale fluid effects with the whitewater simulator. Generate and simulate millions of foam, bubble, and spray particles to give a sense of realism to large bodies of water.
    </td>
  </tr>
<tr>
    <td width="50%" valign="top">
<h3>Viscosity Solver</h3>
Use the high quality viscosity solver to accurately simulate thin silky-smooth liquids, thick fluids that buckle and coil, and anything in between. 
    </td>
    <td>
      <img src="http://rlguy.com/blender_flip_fluids/images/viscosity_solver.jpg">
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="http://rlguy.com/blender_flip_fluids/images/mesh_generation.jpg">
    </td>
    <td valign="top">
<h3>Built-in Mesh Generation</h3>
The built-in mesher generates highly detailed meshes so that your fluid surface is render-ready immediately after simulation. This mesh generator is memory efficient and able to produce meshes containing millions of triangles without requiring massive amounts of RAM.
    </td>
  </tr>
<tr>
<tr>
    <td width="50%" valign="top">
<h3>Fracture Modifier Support</h3>
Create interesting destruction simulations by using the FLIP Fluids addon with the Blender Fracture Modifier branch. The fluid engine is optimized to support fractured objects that may contain hundreds to thousands of individual pieces.
    </td>
    <td>
      <img src="http://rlguy.com/blender_flip_fluids/images/fracture_modifier_support.jpg">
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="http://rlguy.com/blender_flip_fluids/images/excellent_user_experience.jpg">
    </td>
    <td valign="top">
<h3>Excellent User Experience</h3>
The addon interface was designed with a focus on functionality and usability to create a comfortable workflow. View simulation progress, meshes, and statistics in real-time. Pause and resume simulation baking- even after a Blender crash. Create and manage your own preset settings. Quickly apply materials from the fluid material library.
    </td>
  </tr>
<tr>
</table>

## Release Notes

Release notes are only displayed for the most recent version. The complete changelog may be viewed [here](changelog.txt)

#### Version: 0.1.3b

 * Notes:
    * For more detailed info on the following changes, you may view the corresponding issue in the FLIP Fluids issue tracker: https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues
    * To avoid potential errors/problems, please create brand new .blend files when testing this version
<!-- -->
* Added:
    * Added functionality to specify GPU compute device (issue [#7](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/7))
    * Added feature to offset timeline simulation playback (issue [#165](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/165))
    * Added visualization for preview mesh grid to the debug grid view (issue [#160](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/160))
    * Added functionality to enable/disable smooth meshing around obstacles (issue [#158](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/158))
    * Added operators to add/remove selected objects as FLIP Fluid objects (issue [#204](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/204))
    * Added functionality to set amount of influence when adding object velocity to inflow (issue [#220](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/220))
    * Added functionality to set number of emissions per substep for inflow objects (issue [#224](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/224))
    * Added functionality to enable/disable experimental optimization features to the 'FLIP Fluid Advanced' panel
    * Added functionality to set region format for CSV file export (issue [#225](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/225))
    * Added support for deformable meshes when using the 'Add Object Velocity to Inflow' feature (issue [#226](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/226))
<!-- -->
* Changed:
    * Fixed 'Out of memory' error when inflow object is outside of domain (issue [#123](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/123))
    * Reduced crashes while rendering (issue [#34](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/34))
    * Fixed error that would occur if frame was computed too quickly (issue [#143](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/143))
    * Fixed cache mesh stats early text cutoff (issue [#198](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/198))
    * Fluid initial velocity can now be animated (issue [#208](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/208))
    * Fixed error that would occur when a temporary directory does not exist (issue [#217](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/217))
    * Addon will now delete the cache directory when closing an unsaved scene (issue [#215](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/215))
    * Fixed issues related to writing savestate data on network drives (issue [#134](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/134))
    * Fixed bug where animated inflow meshes would not interpolate on substeps (issue [#224](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/224))
	
