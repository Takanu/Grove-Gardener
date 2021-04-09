# Grove Gardener (Blender 2.92 + The Grove 10)

Grove Gardener is (or more, will be) a series of small tools designed to convert trees made using The Grove into optimized, game-ready versions that still preserve many of the same details and shapes as the original.

The Grove is a wonderful tool that creates detailed and very convincing tree models, but i've always found its FAQ segment on Game Engines somewhat misleading - while you can modify a tree's scale you change it's character drastically as your trees have to stay extremely young and basic in shape to meet a polygon count target, and you end up leveraging very little of The Grove's capabilities for trees that don't look great.

What The Grove actually needs to be appropriate for game development is the ability to automatically delete and replace branches with twig planes so you still get detailed tree shapes, and thats what this little addon seeks to do.

## The Tools

### Replace Branches (Work in progress)
This tool simply replaces branches in a tree that are less than a specified thickness to an emitter that you can use to distribute your own branches, solving the big issue with The Grove in game development as it stands.

This works for tree types where smaller branches conform to a similar angle and shape as the branches it is grown from, but this wont work on tree types like the Willow.

In the future id like to also add additional features so that instead of using emitters, it uses planes that conform to the specific curve and shape of the branches it replaces so it can be used with any tree type.  Additionally id like to hook that into the current particle system so you can automatically substitute dead branches with a dead branch plane set.


### Average Normals (to be added)
Using the available tree mesh data, some kind of tool that makes the process of creating an averaged normal mesh to project onto tree planes an easy process.

