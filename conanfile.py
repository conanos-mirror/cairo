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
        if self.settings.os == "Windows":
            self.requires.add("glib/2.58.1@conanos/stable")
            self.requires.add("libpng/1.6.34@conanos/stable")
            self.requires.add("zlib/1.2.11@conanos/stable")
            self.requires.add("pixman/0.34.0@conanos/stable")
            self.requires.add("fontconfig/2.13.0@conanos/stable")
            self.requires.add("freetype/2.9.1@conanos/stable")
            self.requires.add("expat/2.2.5@conanos/stable")

        config_scheme(self)
    
    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("bzip2/1.0.6@conanos/stable")


    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        if self.settings.os == "Linux":
            tarball_name = '{name}-{version}.tar'.format(name=self.name, version=self.version)
            archive_name = '%s.xz' % tarball_name
            url_ = 'http://172.16.64.65:8081/artifactory/gstreamer/%s'%(archive_name)
            #url_ = 'https://www.cairographics.org/releases/%s'%(archive_name)
            tools.download(url_, archive_name)
            
            if self.settings.os == 'Windows':
                self.run('7z x %s' % archive_name)
                self.run('7z x %s' % tarball_name)
                os.unlink(tarball_name)
            else:
                self.run('tar -xJf %s' % archive_name)
            os.rename('cairo-%s' % self.version, self._source_subfolder)
            os.unlink(archive_name)
        
        if self.settings.os == 'Windows':
            url_ = "https://github.com/CentricularK/cairo.git"
            branch_ = "testing/1.15.12"
            git = tools.Git(folder=self.name)
            git.clone(url_, branch=branch_)
            tools.patch(patch_file=self.patch)
            tools.patch(patch_file=self.patch_test)
            os.rename(self.name, self._source_subfolder)
        
    def build(self):
        if self.settings.os == "Linux":
            with tools.chdir(self._source_subfolder):
                with tools.environment_append({
                    'PKG_CONFIG_PATH': ':%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig'
                    ':%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig'
                    %(self.deps_cpp_info['glib'].rootpath,
                    self.deps_cpp_info['libpng'].rootpath,
                    self.deps_cpp_info['zlib'].rootpath,
                    self.deps_cpp_info['pixman'].rootpath,
                    self.deps_cpp_info['fontconfig'].rootpath,
                    self.deps_cpp_info['freetype'].rootpath,)
                    }):
                    self.run('NOCONFIGURE=1 ./autogen.sh')
                    _args = ['--prefix=%s/builddir'%(os.getcwd()), '--libdir=%s/builddir/lib'%(os.getcwd()), '--enable-ft=yes']
                    if self.options.shared:
                        _args.extend(['--enable-shared=yes','--enable-static=no'])
                    else:
                        _args.extend(['--enable-shared=no','--enable-static=yes'])
                    self.run('./configure %s'%(' '.join(_args)))#space
                    self.run('make -j2')
                    self.run('make install')
        
        if self.settings.os == 'Windows':
            pkg_config_paths=[ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") for i in ["glib","libpng","zlib","pixman","fontconfig","freetype","expat"] ]
            prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
            libpath = [ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["libpng","bzip2","zlib", "expat"] ]
            include = [ os.path.join(self.deps_cpp_info[i].rootpath, "include") for i in ["fontconfig"] ]
            meson = Meson(self)
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
        if tools.os_info.is_linux:
            with tools.chdir(self._source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))
        if self.settings.os == 'Windows':
            self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

