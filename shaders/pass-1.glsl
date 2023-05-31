#version 330
#define SHADER_TYPE
#ifdef VERTEX_SHADER
in vec3 vertPos;
in vec3 vertNormal;
out vec3 fragPos;
out vec3 fragNormal;
uniform mat4 mvp;
void main()
{
    gl_Position = mvp * vec4(vertPos, 1.0f);
    fragPos = vertPos;
    fragNormal = vertNormal;
}
#endif
#ifdef FRAGMENT_SHADER
in vec3 fragPos;
in vec3 fragNormal;
out vec3 gPos;
out vec3 gNormal;
void main()
{
    gPos = fragPos;
    gNormal = normalize(fragNormal);
}
#endif