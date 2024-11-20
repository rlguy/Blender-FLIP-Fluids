![image](https://github.com/rlguy/Blender-FLIP-Fluids/assets/4285191/53714857-6f04-45c8-8c97-694e37cfb6b9)

# FLIP Fluids

The **[FLIP Fluids addon](https://blendermarket.com/products/flipfluids?ref=2685)** is a tool that helps you set up, run, and render liquid simulation effects. Our custom built fluid engine is based around the popular FLIP simulation technique that is also found in many other professional liquid simulation tools. The FLIP Fluids engine has been in constant development for over four years with a large focus on tightly integrating the simulator into Blender as an addon. It just feels like a native Blender tool!

With our reputation for delivering high quality software and outstanding customer support, the FLIP Fluids addon is one of the best selling products in the Blender community.

- Over 10,000 copies sold, 5 star rating, excellent value
- No subscriptions, all future updates included
- [Try out our free demo! We're sure you'll like it :)](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/FLIP-Fluids-Demo-Addon)
- [Frequently Asked Questions (FAQ)](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions)
- [What is the difference between Blender's Mantaflow FLIP simulator and the FLIP Fluids addon?](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions#what-is-the-difference-between-blenders-mantaflow-fluid-simulator-and-the-flip-fluids-addon)

Have any questions? Do not hesitate to ask us at support@flipfluids.com!

## Getting the FLIP Fluids Addon

You may purchase the **FLIP Fluids** addon on [official marketplaces where the FLIP Fluids addon is sold](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Official-Marketplaces-of-the-FLIP-Fluids-Addon). Purchasing a license entitles you to the full FLIP Fluids feature set and content, tool support, and helps ensure the continued development of the addon. Thanks to the amazing support of the Blender community, we have been able to further develop the addon on a full-time basis since its initial release in May 2018!

#### Getting Support

You can get support for the **FLIP Fluids** addon by reading the [documentation and wiki](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/wiki) or through the marketplace messaging systems where you have purchased the FLIP Fluids addon product. Support is granted to all customers whom have purchased a license.

## Key Features

See any of our [market place product pages](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Official-Marketplaces-of-the-FLIP-Fluids-Addon#where-to-buy-the-flip-fluids-addon) for information on features.

## System Requirements

- Windows, macOS, or Linux operating system
- Blender 3.1 to 4.3 compatible
- CPU 64-bit Intel® or AMD® or Apple Silicon multi-core processor
- 8 GB RAM minimum, 16 GB of RAM or more is highly recommended

## Release Notes

For release notes, see this page: [Release Notes](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Release-Notes)

## License

This program uses multiple licenses. See the files ```LICENSE_GPLv3.md```, ```LICENSE_MIT.md```, and ```LICENSE_Standard_Royalty_Free.md``` for license details. In General:

- The Blender addon code is licensed under the GPL.
- The FLIP Fluids simulation engine is licensed under the MIT license.
- Some addon content will be using a Standard Royalty Free license. This license may cover content such as [example scene files](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions), media, artwork, data, and features that rely on this content ([ex: Mixbox color blending features](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Mixbox-Installation-and-Uninstallation)). This content will only be included within the paid addon and will not be available on the GitHub project page. The addon is still completely usable without this content.

Source code files will state their license at the top of the file. Assets will include a license file and information in their containing directory.

## Building

To build the FLIP Fluids addon, some programming experience or prior experience building C/C++ applications is strongly recommended. The basics of navigation and executing commands using the command line is also recommended.

Like our FLIP Fluids addon? If you can afford, please consider purchasing a license on an [official marketplace](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Official-Marketplaces-of-the-FLIP-Fluids-Addon) to help support our continued development of the project. Development of the FLIP Fluids addon is funded solely through sales through marketplaces, and as a small team we truly appreciate your support.

### Source Code Dependencies

Installations of the following programs will be needed to build and compile the FLIP Fluids addon:

1. A compiler that supports C++11.
    - Windows: **MinGW** is the only supported compiler for Windows OS.
    - macOS: **Clang** (recommended)
    - Linux: **GCC** (recommended)
2. [CMake](https://cmake.org/) to generate the appropriate solution, project, or Makefiles, for your system.
3. [GNU Make](https://www.gnu.org/software/make/) to compile/build the FLIP Fluids simulation engine.
4. (optional) [Python 3.3+](https://www.python.org/) to use the automated build script.

### Building with automated script

This repository includes an automated build script to help you build and compile the FLIP Fluids addon. Use of this script requires an installation of Python 3.3+. The script will work best if CMake and GNU Make are located in your system PATH variable, but if not, you may also specify their locations when executing the script (run ```python build.py --help``` for help).

To build and compile the FLIP Fluids addon, navigate to the root of the project directory and run:

```
python build.py
```

Once successfully built, the FLIP Fluids addon will be located in the ```build/bl_flip_fluids/``` directory.

### Building without automated script

To build and compile the FLIP Fluids addon without the automated Python script, first copy the ```cmake/CMakeLists.txt``` file to the root of the project directory. The program can then be built and compiled using CMake and GNU Make. Example if your current working directory is located at the project root:

```
mkdir build
cd build
cmake .. -DBUILD_DEBUG=ON
make
cmake .. -DBUILD_DEBUG=OFF
make
```

The above script uses CMake and GNU Make to build the FLIP Fluids engine twice: once for the debug version of the engine, and again for the optimized release version of the engine.

The [CMake Generator](https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html) can be specified by adding the ```-G "[generator]"``` flag. For example, to specify MinGW Makefiles on Windows OS, you can add the CMake flag ```-G "MinGW Makefiles"```.

Once successfully built, the FLIP Fluids addon will be located in the ```build/bl_flip_fluids/``` directory.

## Links

- [Blender Market Page](https://www.blendermarket.com/products/flipfluids)
- [Gumroad Page](https://flipfluids.gumroad.com/l/flipfluids)
- [FlippedNormals Page](https://flippednormals.com/product/the-flip-fluids-addon-for-blender-16173?dst=4DxRZXXT)
- [Documentation and Wiki](https://github.com/rlguy/Blender-FLIP-Fluids/wiki)
- [Bug/Issue Tracker](https://github.com/rlguy/Blender-FLIP-Fluids/issues)
- [FLIP Fluids Homepage](http://flipfluids.com)
- [Twitter](https://twitter.com/flipfluids) | [Instagram](https://www.instagram.com/flip.fluids/) | [Facebook](https://www.facebook.com/FLIPFluids/) | [FLIP Fluids YouTube](https://www.youtube.com/flipfluids) | [BlenderPhysics YouTube](https://www.youtube.com/blenderphysicsvideos)
- Discord Server: https://discord.gg/FLIPFluids
