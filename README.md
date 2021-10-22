# FLIP Fluids

The **[FLIP Fluids addon](https://blendermarket.com/products/flipfluids)** is a tool that helps you set up, run, and render liquid simulation effects. Our custom built fluid engine is based around the popular FLIP simulation technique that is also found in many other professional liquid simulation tools. The FLIP Fluids engine has been in constant development for over four years with a large focus on tightly integrating the simulator into Blender as an addon. It just feels like a native Blender tool!

With our reputation for delivering high quality software and outstanding customer support, the FLIP Fluids addon is one of the best selling products on the Blender Market.

- 6000+ sales, 5 star rating, excellent value
- No subscriptions, all future updates included
- [Try out our free demo! We're sure you'll like it :)](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/FLIP-Fluids-Demo-Addon)
- [Frequently Asked Questions (FAQ)](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions)
- [What is the difference between Blender's Mantaflow FLIP simulator and the FLIP Fluids addon?](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions#what-is-the-difference-between-blenders-mantaflow-fluid-simulator-and-the-flip-fluids-addon)
- Have any questions? Do not hesitate to ask on the [Blender Market](https://blendermarket.com/products/flipfluids) or at support@flipfluids.com!

## Getting the FLIP Fluids Addon

You may purchase the **FLIP Fluids** addon through our product page on the [Blender Market](https://www.blendermarket.com/products/flipfluids). Purchasing a license entitles you to to full FLIP Fluids feature set and content, tool support, and helps ensure the continued development of the addon. Thanks to the amazing support of the Blender community, we have been able to further develop the addon on a full-time basis since our initial release in May 2018!

#### Getting Support

You can get support for the **FLIP Fluids** addon by reading the [documentation and wiki](https://github.com/rlguy/Blender-FLIP-Fluids-Beta/wiki) or through the Blender Market messaging system. Support is granted to all customers whom have purchased a license.

## Key Features

See our [Blender Market product page](https://blendermarket.com/products/flipfluids) for information on features.

## System Requirements

- Windows, MacOS, or Linux operating system
- Blender 2.79 or 2.8+* or 2.9+ (64-bit)
- CPU 64-bit Intel® or AMD® or Apple Silicon multi-core processor
- 8 GB RAM minimum, 16 GB or more of RAM memory is highly recommended

***Blender Support on MacOS:** Due to a MacOS specific [Blender bug](https://developer.blender.org/T68243) in versions 2.80, 2.81, and 2.82, these Blender versions cannot be supported. Blender 2.79 or 2.83+ or 2.9+ are required for MacOS.

## Release Notes

**FLIP Fluids Version 1.0.9** - Our biggest update yet adds new [force field features](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions#force-field-examples) and many more improvements! [See new example scene animations](https://gfycat.com/amusedlongkitfox).

For full release notes, see this page: [Release Notes](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Release-Notes)

## License

This program uses multiple licenses. See the files ```LICENSE_GPLv3.md```, ```LICENSE_MIT.md```, and ```LICENSE_Standard_Royalty_Free.md``` for license details. In General:

- The Blender addon code is licensed under the GPL.
- The FLIP Fluids simulation engine is licensed under the MIT license.
- Some addon content will be using a Standard Royalty Free license. This license may cover content such as [example scene files](https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions), media, artwork, and data. This content will only be included within the paid addon and will not be available on the GitHub project page. The addon is still completely usable without this content.

Source code files will state their license at the top of the file. Assets will include a license file and information in their containing directory.

## Building

To build the FLIP Fluids addon, some programming experience or prior experience building C/C++ applications is recommended. The basics of navigation and executing commands using the command line is also recommended.

Like our FLIP Fluids addon? If you can afford, please consider purchasing a license on the [Blender Market](https://blendermarket.com/products/flipfluids) to help support our continued development of the project. Development of the FLIP Fluids addon is funded solely through sales on the marketplace, and as a small team we truly appreciate your support.

### Source Code Dependencies

There is one dependency to build this program:

1. A compiler that supports C++11.

_WINDOWS OS WARNING: Compilation using MSVC (Microsoft Visual Studio Compiler) is not supported. Building with MSVC will result in errors, performance issues, and incorrect simulation behaviour. The MinGW compiler is the only supported Windows compiler._

Aside from a C++11 compiler, you will also require installations of: 

1. [CMake](https://cmake.org/) to generate the appropriate solution, project, or Makefiles, for your system.
2. [GNU Make](https://www.gnu.org/software/make/) to compile/build the FLIP Fluids simulation engine.
3. (optional) [Python 3.3+](https://www.python.org/) to use the automated build script.

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
- [Documentation and Wiki](https://github.com/rlguy/Blender-FLIP-Fluids/wiki)
- [Bug/Issue Tracker](https://github.com/rlguy/Blender-FLIP-Fluids/issues)
- [FLIP Fluids Homepage](http://flipfluids.com)
- [Development Notes](http://flipfluids.com/blog)
- [Twitter](https://twitter.com/flipfluids) | [Instagram](https://www.instagram.com/flip.fluids/) | [Facebook](https://www.facebook.com/FLIPFluids/) | [YouTube](https://www.youtube.com/flipfluids)
