"""
Generate new dungeons for storymode
"""

import random

_TYPES = ["Other", "Audio", "Image", "Compressed", "Video", "Executable"]
_SEEDSIZE = 63

with open('public/storymode/dungeon.map', 'w') as f:
    seed = random.getrandbits(_SEEDSIZE)
    filetype = random.choice(_TYPES)
    difficulty = random.randint(1, 5)
  
    f.write("%d %s %d" % (seed, filetype, difficulty))
