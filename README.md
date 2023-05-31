# PreIntegratedSSS

An implementation of pre-integrated SSS according to GPU Pro 2, supporting point and directional lights.

Pre-integrated SSS is basically replacing the cosine term in commonplace diffuse with a look-up to the previously calculated texture, using dot product of light direction and normal and surface curvature as texture coordinates.

![Look-up-table](https://github.com/LeonKang130/PreIntegratedSSS/blob/main/look_up_table.png)

Personally I encountered some artifact when using `length(fwidth(normal)) / length(fwidth(position))` directly as the curvature, so I set a lower bound to it.

![Pre-integrated SSS](https://github.com/LeonKang130/PreIntegratedSSS/blob/main/result-scene-gaussian.png)

Due to lack of time, I haven't added shadow or translucency yet(SSS doesn't count for translucency).

Configure scenes via *scenes/\*.json*. There are a few examples in that directory.

Particular options:
- Add simple Blinn-Phong specular by setting "specular-on" as true;
- Use "sum of Gaussians" to render skin texture by setting "equation" as "gaussian";
- Configure effect of SSS by changing "tuneCurvature"(amplify curvature of the model) and "maxCurvature"(maximum curvature in the look-up-table);

Sample scenes:
- Set camera at `(0.0, 1.0, -10.0)` and look at `(0.0, 0.5, 0.0)`. Render model `13.obj`.
- Set camera at `(0.0, 1.0, 8.0)` and look at `(0.0, 0.5, 0.0)`. Render model `3/4.obj`.
