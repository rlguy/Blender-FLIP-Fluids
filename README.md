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

#### Version: 0.1.2b

 * Notes:
    * For more detailed info on the following changes, you may view the corresponding issue in the FLIP Fluids issue tracker: https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues
    * To avoid potential errors/problems, please create brand new .blend files when testing this version
<!-- -->
* Added:
    * Added operator to 'FLIP Fluid Display Settings' panel to enable the whitewater simulation feature (issue [#42](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/42))
    * Added functionality to 'inverse' outflow objects (issue [#80](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/80))
<!-- -->
* Changed:
    * Changed preset info '?' icon to '!' icon (issue [#64](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/64))
    * Cycles visibility restriction settings are now set on domain, fluid, inflow, and outflow objects so that they are not rendered when rendering in the viewport (issue [#44](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/44))
    * Fixed bug where cache meshes wouldn't copy domain object transforms properly (issue [#41](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/41))
    * Particle scale property now has a soft minimum value (issue [#64](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/64))
    * Fixed Python error message when deleting unheld cache files
    * Fixed crash that could happen if the GPU Scalar Field option is disabled (issue [#86](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/86))
    * The simulator will now select the most 'powerful' GPU by default (issue [#6](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/6))
    * Fixed whitewater issues with AMD GPU hardware (issue [#78](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/78))
    * Fixed crash that would occur if an obstacle mesh contained loose geometry (issue [#91](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues/91))
