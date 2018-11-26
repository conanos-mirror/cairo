#include <cstdlib>
#include <iostream>
#include <cairo/cairo.h>
#include <cairo/cairo-version.h>

int main()
{
    std::cout << "cairo version is " << cairo_version_string() << std::endl;
    return EXIT_SUCCESS;
}
