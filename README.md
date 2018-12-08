# Human-Segmentation-Using-Unsupervised-Clustering
Tool to segment human anatomy using unsupervised clustering

# Define inputs and outputs
* Input: PLY file of a 3D human model
* Output: Labels of PLY points. Likely each label will be a different color.

# Method 
1. Input PLY file. Clean and translate to origin. 
2. Sort by y-axis (frontal plane) and bin y-values to the nearest 1mm.
3. Generate n horizontal slices at 1mm separation. For each slice, run MeanShift to label points.
  * Inputs: X, Y, Z points
  * Parameters: separation (1mm)
  * Output: k labels * n horizontal slices
4. Generate new features from labels:
  * Shoelace area
  * Centroid
  * Min
  * Max
5. Run MeanShift with features from (4) to cluster the previous clusters
  * Inputs: Shoelace area, Centroid, Min, Max
  * Parameters: separation (1mm)
