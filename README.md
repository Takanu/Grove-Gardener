# Grove Gardener (Blender 2.92 + The Grove 10)

Grove Gardener is (or more, will be) a series of small tools designed to convert trees made using The Grove into optimized, game-ready versions that still preserve many of the same details and shapes as the original.

The Grove is a wonderful tool that creates detailed and very convincing tree models, but i've always found its FAQ segment on Game Engines somewhat misleading - while you can modify a tree's scale you change it's character drastically as your trees have to stay extremely young and basic in shape to meet a polygon count target, and you end up leveraging very little of The Grove's capabilities for trees that don't look great.

What The Grove actually needs to be appropriate for game development is the ability to automatically delete and replace branches with twig planes so you still get detailed tree shapes, and thats what this little addon seeks to do.

## Important Notice
This is **not a standalone addon** as it would require copying and hosting all of The Grove code here and the creator of the plugin deserves support for their awesome work, this repository only contains code modifications for The Grove and the instructions for how to add them to your own copy of The Grove.

The Grove is a one-time purchase and you'll get all future updates for free, making it a great investment - https://www.thegrove3d.com/.

---

# The Tools

### Replace Branches (Work in progress)
This tool adds a new twig type - frond.  The frond mesh set will automatically replace branches that are lower than a certain thickness and it will still bend and conform to the path the original branch would have taken.

### Simplify Edge Loops (Work in progress)
The Grove adds a lot of edge loops that trees don't always need and this small tool automatically removes some of them to reduce the polygon count.

### Average Normals (to be added)
Using the available tree mesh data, some kind of tool that makes the process of creating an averaged normal mesh to project onto tree planes an easy process.

