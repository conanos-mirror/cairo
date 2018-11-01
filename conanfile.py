from conans import ConanFile, CMake, tools
import os

class CairoConan(ConanFile):
    name = "cairo"
    version = "1.14.12"
    description = "Cairo is a 2D graphics library with support for multiple output devices"
    url = "https://github.com/conanos/cairo"
    homepage = "https://cairographics.org/"
    license = "GNU LGPL 2.1"
    exports = ["LICENSE.md"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = ("glib/2.58.0@conanos/dev","libpng/1.6.34@conanos/dev","zlib/1.2.11@conanos/dev",
    "pixman/0.34.0@conanos/dev","fontconfig/2.12.6@conanos/dev","freetype/2.9.0@conanos/dev",)

    source_subfolder = "source_subfolder"

    def source(self):
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
        os.rename('cairo-%s' % self.version, self.source_subfolder)
        os.unlink(archive_name)
        
    def build(self):
        with tools.chdir(self.source_subfolder):
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
                _args = ['--prefix=%s/builddir'%(os.getcwd()), '--libdir=%s/builddir/lib'%(os.getcwd())]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes'])
                self.run('./configure %s'%(' '.join(_args)))#space
                self.run('make -j2')
                self.run('make install')

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

