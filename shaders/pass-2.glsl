#version 450
#define SHADER_TYPE
#define SPECULAR_OPTION
#ifdef VERTEX_SHADER
in vec3 vertPos;
out vec2 fragCoord;
void main()
{
    gl_Position = vec4(vertPos, 1.0);
    fragCoord = vertPos.xy;
}
#endif
#ifdef FRAGMENT_SHADER
uniform sampler2D lookUpTable;
uniform sampler2D gPos;
uniform sampler2D gNormal;
uniform float tuneCurvature = 1.0f;
uniform float minCurvature = 1.0f;
in vec2 fragCoord;
out vec3 fragColor;
const vec3 cameraPos = vec3(0.0, 1.0, 8.0);
struct PointLight
{
    vec3 emission;
    vec3 position;
};
struct DirectionLight
{
    vec3 emission;
    vec3 direction;
};
layout (std140, binding=0) uniform PointLightBuffer
{
    PointLight pointLights[32];
};
layout (std140, binding=1) uniform DirectionLightBuffer
{
    DirectionLight directionLights[32];
};
uniform int numPointLights = 0;
uniform int numDirectionLights = 0;
vec3 linearToSRGB(vec3 color)
{
    vec3 a = 1.055 * pow(color, vec3(1.0 / 2.4)) - 0.055;
    vec3 b = 12.92 * color;
    vec3 cut_off = vec3(lessThan(color, vec3(0.00031308)));
    return clamp(mix(a, b, cut_off), 0.0, 1.0);
}
void main()
{
    vec2 uv = fragCoord * 0.5 + 0.5;
    vec3 fragNormal = normalize(texture(gNormal, uv).xyz);
    vec3 fragPos = texture(gPos, uv).xyz;
    float curvature = max(length(fwidth(fragNormal)) / length(fwidth(fragPos)), minCurvature) * tuneCurvature;
    vec3 color = vec3(0.0f);
    vec3 viewDir = normalize(cameraPos - fragPos);
    for(int i = 0; i < numPointLights; i++)
    {
        PointLight light = pointLights[i];
        vec3 lightDir = normalize(light.position - fragPos);
        vec3 halfDir = normalize(viewDir + lightDir);
        float NDotL = dot(fragNormal, lightDir);
        vec3 diffuse = pow(texture(lookUpTable, vec2(0.5 * NDotL + 0.5, curvature)).xyz, vec3(2.2f)) * light.emission;
        #ifdef WITH_SPECULAR
        vec3 specular = pow(max(dot(halfDir, fragNormal), 0.0f), 256.0f) * light.emission;
        #else
        vec3 specular = vec3(0.0f);
        #endif
        color += diffuse + specular;
    }
    for(int i = 0; i < numDirectionLights; i++)
    {
        DirectionLight light = directionLights[i];
        vec3 lightDir = normalize(light.direction);
        vec3 halfDir = normalize(viewDir + lightDir);
        float NDotL = dot(fragNormal, lightDir);
        vec3 diffuse = pow(texture(lookUpTable, vec2(0.5 * NDotL + 0.5, curvature)).xyz, vec3(2.2f)) * light.emission;
        #ifdef WITH_SPECULAR
        vec3 specular = pow(max(dot(halfDir, fragNormal), 0.0f), 256.0f) * light.emission;
        #else
        vec3 specular = vec3(0.0f);
        #endif
        color += diffuse + specular;
    }
    fragColor = linearToSRGB(color);
}
#endif