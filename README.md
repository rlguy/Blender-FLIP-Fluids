# FLIP Fluids

**FLIP Fluids** is a powerful liquid simulation plugin that gives you the ability to create high quality fluid effects all within [Blender](https://www.blender.org/), the free and open source 3D creation suite. Created by Ryan Guy and Dennis Fassbaender.

The core fluid engine, a modern FLIP-based fluid solver, has been under development for over three years with over a year of development focused on tightly integrating the simulator into Blender as an addon.

The **FLIP Fluids** simulator was created to improve on many aspects of Blender's internal Elbeem fluid simulation system such as speed, performance, accuracy, customizability, and user experience. We use a familiar and intuitive simulation workflow, so if you have experience with the internal fluid simulator or other fluid simulation software, you will be able to get yourself up and running with **FLIP Fluids** in no time!

## Getting the FLIP Fluids Addon

You may purchase the **FLIP Fluids** addon on the [Blender Market](https://www.blendermarket.com/products/flipfluids). Purchasing a license entitles you to to full FLIP Fluids feature set and content, tool support, and helps ensure the continued development of the addon.

#### Getting Support

You can get support for the **FLIP Fluids** addon by reading the [documentation and wiki](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/wiki) or through the Blender Market messaging system. Support is granted to all customers whom have purchased a license.

## FLIP Fluids Beta

A closed beta testing phase involving over 250 testers ran from February 13th to April 28th (2018). The project is no longer in beta. You may access old beta material here: [FLIP Fluids Beta Information](../../wiki/FLIP-Fluids-Beta-Information-and-Resources). Some beta resources may no longer available.

## Key Features

<table>
  <tr>
    <td width="50%" valign="top">
<h3>High Performance</h3>
The core fluid engine, written in C++, is designed for running high performance computations and massive physics calculations efficiently. Multithreaded and extensively optimized, this simulator is built for speed.
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
<h3>Whitewater Effects</h3>
Create awesome large scale fluid effects with the whitewater simulator. Generate and simulate millions of foam, bubble, and spray particles to give a sense of realism to large bodies of water.
    </td>
  </tr>
<tr>
    <td width="50%" valign="top">
<h3>Viscosity Effects</h3>
Use the highly accurate viscosity solver to simulate thin silky-smooth liquids, thick fluids that buckle and coil, and anything in between.
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
    <td width="50%" valign="top">
<h3>Stable, Reliable, and Built for You</h3>
We ran a closed beta testing phase involving over 250 testers to ensure that this complex simulation system is reliable, intuitive, and ready for you to use in your projects. We gathered your feedback and added your suggestions. This addon is built for you!
    </td>
    <td>
      <img src="http://rlguy.com/blender_flip_fluids/images/tested.jpg">
    </td>
  </tr>
</table>
	
### More Features

<ul>
    <li type="square"><strong>Simulation</strong>
        <ul>
            <li><span style="font-size: 13px;">Pause a simulation and resume baking at your convenience. Any simulation can be continued from the last baked frame even after a crash or computer shutdown.</span></li>
            <li><span style="font-size: 13px;">Set length of animation manually or automatically by framerate.</span></li>
            <li><span style="font-size: 13px;">Nearly all simulation settings can be keyframe animated.</span></li>
            <li><span style="font-size: 13px;">Hover over any setting to view a tooltip description. Detailed settings documentation and tips are also available on the <a href="https://github.com/rlguy/Blender-FLIP-Fluids-Beta/wiki" rel="noopener noreferrer" target="_blank">Wiki</a>.</span></li>
            <li><span style="font-size: 13px;">Want to keep the same level of simulation detail while resizing the domain? Lock the simulation voxel size and the addon will automatically adjust grid resolution as you resize the domain.</span></li>
            <li><span style="font-size: 13px;">Manage your scene cache directory. Operators will help you rename, move, copy, or delete your cache files.</span></li>
            <li><span style="font-size: 13px;">Advanced settings for power users who want to experiment with simulation accuracy and performance.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Whitewater Simulation</strong>
        <ul>
            <li><span style="font-size: 13px;">Control the amount of whitewater generated at wavecrests and in areas of high turbulence.</span></li>
            <li><span style="font-size: 13px;">Control how foam is carried along the fluid surface: In tight streaks, or diffuse and spread-out?</span></li>
            <li><span style="font-size: 13px;">Control how bubbles rise to the surface and how bubbles are advected with the fluid.</span></li>
            <li><span style="font-size: 13px;">Control amount of drag on spray particles as they fall to the fluid surface.</span></li>
            <li><span style="font-size: 13px;">Set percentages of foam/bubble/spray particles for display and rendering.</span></li>
            <li><span style="font-size: 13px;">Render whitewater particles with a simple icosphere or use your own custom object.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Mesh Generator</strong>
        <ul>
            <li><span style="font-size: 13px;">Adjust particle size for the particle-to-mesh surface generator.</span></li>
            <li><span style="font-size: 13px;">Create high detail meshes by increasing the subdivision level.</span></li>
            <li><span style="font-size: 13px;">Generate meshes that wrap smoothly around curved surfaces.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Presets and Materials</strong>
        <ul>
            <li><span style="font-size: 13px;">Save your own custom default domain settings.</span></li>
            <li><span style="font-size: 13px;">Create and manage domain presets.</span></li>
            <li><span style="font-size: 13px;">Organize presets into packages and add custom thumbnail images.</span></li>
            <li><span style="font-size: 13px;">Export and share preset packages.</span></li>
            <li><span style="font-size: 13px;">Apply multiple presets at once using the preset stack.</span></li>
            <li><span style="font-size: 13px;">Quickly apply materials from the fluid material library.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Simulation Stats</strong>
        <ul>
            <li><span style="font-size: 13px;">View simulation, timing, and mesh stats for the entire cache or an individual frame.</span></li>
            <li><span style="font-size: 13px;">Export stats to CSV format and create your own detailed graphs.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Debugging Tools</strong>
        <ul>
            <li><span style="font-size: 13px;">Visualize the simulation and meshing grid.</span></li>
            <li><span style="font-size: 13px;">Visualize fluid particles and velocities.</span></li>
            <li><span style="font-size: 13px;">Visualize how the simulator 'sees' your obstacle objects to diagnose issues with meshes.</span></li>
            <li><span style="font-size: 13px;">View detailed simulation progress in the Blender system console.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Obstacle Objects</strong>
        <ul>
            <li><span style="font-size: 13px;">Support for animated obstacle objects.</span></li>
            <li><span style="font-size: 13px;">Turn obstacle meshes <em>'inside-out'</em> to contain fluid inside of the mesh.</span></li>
            <li><span style="font-size: 13px;">Accurate fluid-solid interaction against curved surfaces.</span></li>
            <li><span style="font-size: 13px;">Control amount of fluid friction against the obstacle surface.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Fluid and Inflow Objects</strong>
        <ul>
            <li><span style="font-size: 13px;">Support for animated inflow objects.</span></li>
            <li><span style="font-size: 13px;">Manually set inflow velocity, or set velocity towards a target object.</span></li>
            <li><span style="font-size: 13px;">Add inflow object velocity to the emitted fluid for realistic animated inflows.</span></li>
        </ul>
    </li>
    <li type="square"><strong>Outflow Objects</strong>
        <ul>
            <li><span style="font-size: 13px;">Support for animated outflow objects.</span></li>
            <li><span style="font-size: 13px;">Control whether outflow objects remove fluid particles or whitewater particles.</span></li>
            <li><span style="font-size: 13px;">Control whether outflows will remove fluid entering the object or leaving the object.</span></li>
        </ul>
    </li>
</ul>

## System Requirements

- Windows 7, Windows 8, Windows 8.1, or Windows 10
- Blender 2.79 (64-bit)
- CPU 64-bit Intel® or AMD® multi-core processor
- 8 GB RAM minimum, 16 GB or more of RAM memory is highly recommended
- OpenCL™ capable graphics card

#### Mac OS X and Linux support

At this moment, support for Mac OS X and Linux is **experimental**. This means that the addon has not yet undergone extensive testing on OS X and Linux operating systems.

If you are planning to purchase the addon for use on OS X or Linux we first **highly recommend** trying the [FLIP Fluids Demo](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/FLIP-Fluids-Demo-Addon) to test if the simulator will work on your system.

## License

This program uses multiple licenses. See the files ```LICENSE_GPLv3.md```, ```LICENSE_MIT.md```, and ```LICENSE_Standard_Royalty_Free.md``` for license details. In General:

- The Blender addon code is licensed under the GPL.
- The fluid engine is licensed under the MIT license.
- Some addon content will be using a Standard Royalty Free license. This license may cover content such as media (images/textures/videos), Blend files, materials, presets. This content will only be included within the paid addon and will not be available on the GitHub project page.

Source code files will state their license at the top of the file. Assets will include a license file and information in their containing directory.

## Links

- [Blender Market Page](https://www.blendermarket.com/products/flipfluids)
- [Documentation and Wiki](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/wiki)
- [Bug/Issue Tracker](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/issues)
- [BlenderPhysics Page](http://blenderphysics.com/#filter=.FLIP-Fluids)
- [Facebook Page](https://www.facebook.com/FLIPFluids/) | [Twitter](https://twitter.com/flipfluids)
