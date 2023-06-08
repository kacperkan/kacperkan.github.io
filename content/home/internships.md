
+++
# Internships widget.
widget = "accomplishments"  # See https://sourcethemes.com/academic/docs/page-builder/
headless = true  # This file represents a page section.
active = true  # Activate this widget? true/false
weight = 40  # Order that this section will appear.

title = "Internships"
subtitle = ""

# Date format
#   Refer to https://sourcethemes.com/academic/docs/customization/#date-format
date_format = "Jan 2006"

# Accomplishments.
#   Add/remove as many `[[item]]` blocks below as you like.
#   `title`, `organization` and `date_start` are the required parameters.
#   Leave other parameters empty if not required.
#   Begin/end multi-line descriptions with 3 quotes `"""`.

[[item]]
  organization = "Microsoft Research Cambridge"
  date_start = "2022-07-01"
  date_end = "2022-09-26"
  description = "Working on realistic 3D human avatars. I extended [VolTeMorph](https://arxiv.org/abs/2208.00949) to incorporate more realistic facial details that from performing different expressions. Our results have been published at CVPR 2023 conference. You can read more about it [here](https://blendfields.github.io/)."

[[item]]
  organization = "University of British Columbia"
  date_start = "2021-06-01"
  date_end = "2021-12-01"
  description = "I have developed a method that enables controlling neural radiance fields from sparse, manual annotations. Both annotations are coarse segmentation masks of the areas you want to control, and leave the neural network to learn how to propagate that information across 3D. The work was published at CVPR 2022. You can read more about that [here](https://conerf.github.io/)."

+++
