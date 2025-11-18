![image](https://github.com/rlguy/Blender-FLIP-Fluids/assets/4285191/53714857-6f04-45c8-8c97-694e37cfb6b9)

- [FLIP Fluids](#flip-fluids)
  * [Getting the FLIP Fluids Addon](#getting-the-flip-fluids-addon)
  * [Key Features](#key-features)
  * [System Requirements](#system-requirements)
  * [Release Notes](#release-notes)
  * [License](#license)
  * [Building](#building)
  * [Links](#links)

# FLIP Fluids

The **[FLIP Fluids addon](https://superhivemarket.com/products/flipfluids?ref=2685)** is a tool that helps you set up, run, and render liquid simulation effects. Our custom built fluid engine is based around the popular FLIP simulation technique that is also found in many other professional liquid simulation tools. The FLIP Fluids engine has been in constant development since 2016 with a large focus on tightly integrating the simulator into Blender as an addon. It just feels like a native Blender tool!

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
- Blender 4.5 to 5.0 compatible
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

To build the FLIP Fluids addon and its external dependencies, some programming experience and prior experience in building C/C++ applications with CMake is strongly recommended. Some familiarity with the C/C++ compiling, linking, and building process is recommended for debugging and resolving any errors or warnings that are encountered.

Do you like our FLIP Fluids addon? If you can afford, please consider purchasing a license on an [official marketplace](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Official-Marketplaces-of-the-FLIP-Fluids-Addon) to help support our continued development of the project. Development of the FLIP Fluids addon is funded solely through through marketplace sales, and as a small team we truly appreciate your support.

### Source Code Dependencies

Installations of the following programs and dependencies will be needed to build and compile the FLIP Fluids addon:

**Required**:
1. A compiler that supports C++17.
    - Windows: **MinGW** is the only supported compiler for Windows OS.
    - macOS: **Clang** (recommended)
    - Linux: **GCC** (recommended)
2. [CMake](https://cmake.org/) to generate the appropriate solution, project, or Makefiles, for your system.
3. [GNU Make](https://www.gnu.org/software/make/) to compile/build the FLIP Fluids simulation engine.
4. [Alembic](https://github.com/alembic/alembic) and its external dependencies:
    - [Imath 3](https://github.com/AcademySoftwareFoundation/Imath)

**Optional:**
1. [Python 3.3+](https://www.python.org/) to use the automated build script.

### Building with automated script

This repository includes an automated build script to help you build and compile the FLIP Fluids addon. Use of this script requires an installation of Python 3.3+. 

To build, compile, and package the FLIP Fluids addon, navigate to the root of the project directory and run:

```
python build.py
```

Once successfully built, the FLIP Fluids addon and installation .zip file will be located in the ```build/bl_flip_fluids/``` directory. See [Addon Installation Guide](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Addon-Installation-and-Uninstallation).

**Notes:**
- The build script will work best if CMake and GNU Make are located in your system PATH variable, but if not, you may also specify their locations when executing the script with the ```-cmake-path path/to/cmake``` and ```-make-path path/to/make``` flags.
- The simulator relies on the _**Alembic**_ and _**Imath 3**_ external dependencies. If these shared libraries and each of their own dependencies are not located in your system PATH variable, they should be packaged within the addon by providing a list of filepaths with the ```-package-dependencies path/to/lib1 path/to/lib2``` flag.
- run ```python build.py --help``` for help.

### Building without automated script

To build and compile the FLIP Fluids addon, navigate to the root of the project directory and run:

**Windows**

```
mkdir build
cd build
cmake .. -G "MinGW Makefiles"
make
```

**Linux/MacOS**

```
mkdir build
cd build
cmake ..
make
```

Once successfully built, the FLIP Fluids addon will be located in the ```build/bl_flip_fluids/``` directory.

**Notes:**
- To create an addon installation file, zip the ```build/bl_flip_fluids/flip_fluids_addon``` directory using an archive utility of your choice. See [Addon Installation Guide](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Addon-Installation-and-Uninstallation).
- The simulator relies on the _**Alembic**_ and _**Imath 3**_ external dependencies. If these shared libraries and each of their own dependencies are not located in your system PATH variable, they should be packaged within the addon by copying the libraries to the ```build/bl_flip_fluids/flip_fluids_addon/ffengine/lib/``` directory.

## Links

- Marketplaces
    - [Superhive (_formerly Blender Market_)](https://superhivemarket.com/products/flipfluids?ref=2685)
    - [Gumroad](https://flipfluids.gumroad.com/l/flipfluids)
    - [FlippedNormals](https://flippednormals.com/product/the-flip-fluids-addon-for-blender-16173?dst=4DxRZXXT)
- [Documentation and Wiki](https://github.com/rlguy/Blender-FLIP-Fluids/wiki)
- [Bug/Issue Tracker](https://github.com/rlguy/Blender-FLIP-Fluids/issues)
- [FLIP Fluids Homepage](http://flipfluids.com)
- [Instagram](https://www.instagram.com/flip.fluids/) | [X (Twitter)](https://x.com/flipfluids) | [Facebook](https://www.facebook.com/FLIPFluids/) | [FLIP Fluids YouTube](https://www.youtube.com/flipfluids) | [BlenderPhysics YouTube](https://www.youtube.com/blenderphysicsvideos)
- Discord Server: https://discord.gg/FLIPFluids
