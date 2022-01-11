---
title: "Representing Point Clouds with Generative Conditional Invertible Flow Networks"
authors:
- Michał Stypułkowski
- admin
- Maciej Zamorski
- Maciej Zięba
- Tomasz Trzciński
- Jan Chorowski
date: "2021-07-17T00:00:00Z"
doi: "10.1016/j.patrec.2021.07.001"

# Schedule page publish date (NOT publication's date).
publishDate: "2021-07-17T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["2"]

# Publication name and optional abbreviated publication name.
publication: In *Pattern Recognition Letters vol. 150, pp 26-32*
publication_short: In *Pattern Recongition Letters*

abstract: "In this paper, we propose a simple yet effective method to represent point clouds as sets of samples drawn from a cloud-specific probability distribution. This interpretation matches intrinsic characteristics of point clouds: the number of points and their ordering within a cloud is not important as all points are drawn from the proximity of the object boundary. We postulate to represent each cloud as a parameterized probability distribution of points in space, which is defined by a generative neural network. The network operates by composing several spatial transformations of point locations. Once trained, it provides a natural framework for point cloud manipulation. For instance we can decouple cloud shape from its orientation and provide routines for aligning a new cloud into a default spatial orientation. To exploit similarities between same-class objects and to improve model performance, we turn to weight sharing: networks that model densities of points belonging to objects in the same family share all parameters with the exception of a small, object-specific embedding vector. We show that these embedding vectors capture semantic relationships between objects. Our method leverages generative invertible flow networks to learn embeddings as well as to generate point clouds. Thanks to this formulation and contrary to similar approaches, we are able to train our model in an end-to-end fashion. As a result, our model offers competitive or superior quantitative results on benchmark datasets, while enabling unprecedented capabilities to perform cloud manipulation tasks, such as point cloud registration and regeneration, by a generative network."

# Summary. An optional shortened abstract.
summary: "In this paper, we propose a simple yet effective method to represent
point clouds as sets of samples drawn from a cloud-specific probability
distribution. Our model offers competitive or superior quantitative results on
benchmark datasets, while enabling unprecedented capabilities to perform cloud
manipulation tasks, such as point cloud registration and regeneration, by a
generative network."

tags:
featured: true

links:
# - name: Custom Link
#   url: http://example.org
url_pdf: https://www.sciencedirect.com/science/article/pii/S0167865521002294
url_code: https://github.com/MStypulkowski/CIF
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder. 
image:
  caption: 'Samples generated with the proposed normalizing flow'
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
