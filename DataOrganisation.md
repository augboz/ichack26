# Table coordinate space

## Idea 1: straight line segmentation

honestly not a fan of this idea, I prefer rectangles.

## Idea 2: Rectangle mapping

Have a rectangle with the 4 corner coordinates stored. If a person is detected within that rectangle, they are occupying the space.

For both ideas, map rectangle/ regions to their table ID. Table ID is completely unique to each table and will be used for frontend and backend.

# Table usage tracking

## Idea 1: Sampling

Sample every N second and check which tables are flagged as occupied for a number of samples that exceed some threshold.

For example, if we sample every second, then a requirement may be to have 30 distinct samples at the given disk for occupation.

# Object classification

There are two types of objects that we are interested in, humans and objects that imply occupation of space even without human presence.

Human: Can be classified by looking for hands/ arms, or top of head, or face.

Other space occupiers: Laptop, iPad, Notepad. Things like Waterbottles do NOT count.