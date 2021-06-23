# Grove Gardener (Blender 2.92 + The Grove 10)

Grove Gardener is an addon that modifies the popular tree generation addon The Grove to make it suitable for growing game engine-ready trees, letting you use the same powerful tools and algorithms that it has to offer.

The Grove is a wonderful tool that creates detailed and very convincing tree models for VFX and pre-rendered visuals, but i've always found its FAQ segment on Game Engines rather misleading - while you can modify a tree's scale you change it's character drastically as your trees have to stay extremely young and basic in shape to meet a polygon count target, and you end up leveraging very little of The Grove's capabilities for trees that don't look great.

What The Grove actually needs to be appropriate for game development is the ability to automatically delete and replace branches with texture planes so you still get detailed tree shapes, and this addon does that and more to get you great looking trees that work for games.

## IMPORTANT!
This is **not a standalone addon** as it would require copying and hosting all of The Grove code here and the creator of the plugin deserves support for their awesome work, this repository contains a set of modifications with instructions that you will need to follow to modify your own copy of The Grove, as well as an installable addon that provides the interface to Grove Gardener's extra tools.  The code i've included that is from The Grove has been minimized to only 2 functions as they are ones I have had to modify in order for this to work.

Also note that while ive put a lot of work into this to get many of the details right, know that *this is still a prototype and that unless you have lots of disposable income you should carefully consider purchasing The Grove* if your only use-case is to use my set of tools on it as 140 euros (as of posting) is not cheap.

The Grove is a one-time purchase however and you'll get all future updates for free - https://www.thegrove3d.com/.


---

# Features

### Replace Branches
This tool adds a new twig type - frond.  Set a Frond Collection and Grove Gardener will automatically replace twigs that are lower than the thickness threshold you set with one of the fronds from that collection.  The replacements are picked by the length of your meshes in order to find the best fit.

### Simplify Edge Loops
The Grove adds a lot of edge loops that trees don't always need and this small tool automatically removes some of them to reduce the polygon count.

### Normal Reprojection
Using the available tree mesh data, some kind of tool that makes the process of creating an averaged normal mesh to project onto tree planes an easy process.

### Extra Vertex Layers (WIP)
Grove Gardener adds Tree Height, Distance to Trunk, Distance to Frond and Branch Index vertex sets for baking, ready to use for wind shaders.

# Future Plans

* Extra Branch Replacement Modes
* Unity Template Shader
* Particle Baking
* Billboard Texturing


## Limitations
If you use The Grove for VFX, know that **adding Grove Gardener modifications to it will prevent you from recording Growth and Wind animations**, though everything else will work as normal.