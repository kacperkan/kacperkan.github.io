---
title: "TrajeVAE: Controllable Human Motion Generation from Trajectories"
authors:
- admin
- Marek Kowalski
- Tomasz Trzciński
date: "2021-11-24T00:00:00Z"
doi: ""

# Schedule page publish date (NOT publication's date).
publishDate: "2021-11-24T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["4"]

# Publication name and optional abbreviated publication name.
publication: In *arXiv*
publication_short: In *arXiv*

abstract: "The creation of plausible and controllable 3D human motion animations is a long-standing problem that requires a manual intervention of skilled artists. Current machine learning approaches can semi-automate the process, however, they are limited in a significant way: they can handle only a single trajectory of the expected motion that precludes fine-grained control over the output. To mitigate that issue, we reformulate the problem of future pose prediction into pose completion in space and time where multiple trajectories are represented as poses with missing joints. We show that such a framework can generalize to other neural networks designed for future pose prediction. Once trained in this framework, a model is capable of predicting sequences from any number of trajectories. We propose a novel transformer-like architecture, TrajeVAE, that builds on this idea and provides a versatile framework for 3D human animation. We demonstrate that TrajeVAE offers better accuracy than the trajectory-based reference approaches and methods that base their predictions on past poses. We also show that it can predict reasonable future poses even if provided only with an initial pose."

# Summary. An optional shortened abstract.
summary: "We present a novel method for controllable human animation generation.
It is the first method that enables generating sequences from any number of
motion trajectories, allowing a fine-grained control over the animation. "

tags:
featured: false

links:
- name: Project Page
  url: 'https://trajevae.github.io/'
url_pdf: 'https://trajevae.github.io/trajevae.pdf'
url_code: ''
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder. 
image:
  caption: 'Scene of human animations generated with TrajeVAE'
  focal_point: "Smart"
  preview_only: false

# Associated Projects (optional).
#   Associate this publication with one or more of your projects.
#   Simply enter your project's folder or file name without extension.
#   E.g. `internal-project` references `content/project/internal-project/index.md`.
#   Otherwise, set `projects: []`.
projects:
- phd

# Slides (optional).
#   Associate this publication with Markdown slides.
#   Simply enter your slide deck's filename without extension.
#   E.g. `slides: "example"` references `content/slides/example/index.md`.
#   Otherwise, set `slides: ""`.
slides: ""
---

