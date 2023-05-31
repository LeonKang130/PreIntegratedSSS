# PreIntegratedSSS

An implementation of pre-integrated SSS according to GPU Pro 2, supporting point and directional lights.

Configure scenes via *scenes/\*.json*. There are a few examples in that directory.

Particular options:
- Add simple Blinn-Phong specular by setting "specular-on" as true;
- Use "sum of Gaussians" to render skin texture by setting "equation" as "gaussian";
- Configure effect of SSS by changing "tuneCurvature"(amplify curvature of the model) and "maxCurvature"(maximum curvature in the look-up-table);
