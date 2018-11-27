from conans import ConanFile, CMake, tools
import os
from conanos.build import config_scheme
from conans import Meson

class CairoConan(ConanFile):
    name = "cairo"
    version = "1.15.12"
    description = "Cairo is a 2D graphics library with support for multiple output devices"
    url = "https://github.com/CentricularK/cairo"
    homepage = "https://cairographics.org/"
    license = "GNU LGPL 2.1"
    patch = "meson-build-freetype-version.patch"
    patch_test = "cairo-test-constructors-gbk-error.patch"
    exports = ["COPYING",patch, patch_test]
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = { 'shared': False, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def requirements(self):
        self.requires.add("glib/2.58.1@conanos/stable")
        self.requires.add("libpng/1.6.34@conanos/stable")
        self.requires.add("zlib/1.2.11@conanos/stable")
        self.requires.add("pixman/0.34.0@conanos/stable")
        self.requires.add("fontconfig/2.13.0@conanos/stable")
        self.requires.add("freetype/2.9.1@conanos/stable")            

        config_scheme(self)
    
    def build_requirements(self):
        self.build_requires("bzip2/1.0.6@conanos/stable")
        if self.settings.os == "Windows":
            self.build_requires("expat/2.2.5@conanos/stable")
        if self.settings.os == "Linux":
            self.build_requires("libuuid/1.0.3@bincrafters/stable")


    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        url_ = "https://github.com/CentricularK/cairo.git"
        branch_ = "testing/1.15.12"
        git = tools.Git(folder=self.name)
        git.clone(url_, branch=branch_)
        tools.patch(patch_file=self.patch)
        if self.settings.os == 'Windows':
            tools.patch(patch_file=self.patch_test)
        os.rename(self.name, self._source_subfolder)
        
    def build(self):
        pkg_config_paths=[ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") for i in ["glib","libpng","zlib","pixman","fontconfig","freetype"] ]
        prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
        meson = Meson(self)
        include = [ os.path.join(self.deps_cpp_info[i].rootpath, "include") for i in ["fontconfig"] ]
        libpath = [ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["bzip2"] ]
        if self.settings.os == "Linux":
            pkg_config_paths.extend([ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") for i in ["bzip2","libuuid"] ])
            include.extend( [ os.path.join(self.deps_cpp_info["freetype"].rootpath, "include","freetype2") ] )
            with tools.environment_append({
                "C_INCLUDE_PATH" : include,
                "LD_LIBRARY_PATH" : os.pathsep.join(libpath)
                }):
                meson.configure(defs={'prefix' : prefix, 'libdir':'lib'},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))
        
        if self.settings.os == 'Windows':
            pkg_config_paths.extend([ os.path.join(self.deps_cpp_info["expat"].rootpath, "lib", "pkgconfig") ])
            libpath.extend( [ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["libpng","zlib", "expat"] ] )
            with tools.environment_append({
                "INCLUDE" : os.pathsep.join(include + [os.getenv('INCLUDE')]),
                'LIB'  : os.pathsep.join(libpath + [os.getenv('LIB')]),
                }):
                meson.configure(defs={'prefix' : prefix},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

