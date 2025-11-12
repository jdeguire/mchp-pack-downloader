#! /usr/bin/env python3
#
# Copyright (c) 2025, Jesse DeGuire
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# #####
#
# mchp-pack-downloader.py
#
# This is a script to automate downloading device packs from Microchip's packs repository at
# https://packs.download.microchip.com/. For now, this script will download only packs for 32-bit ARM
# devices because this is meant to be used with the 'buildMchpClang.py' script. This will also look
# for and download only the latest versions of packs. If you are building a toolchain, then you
# should make an archive of your sources and packs so you can build those at any time in the future.
#
# You can modify what packs this script will look for by editing the 'should_get_this_pack()' function.
#

from html.parser import HTMLParser
import urllib.request

# Edit this if you have a different pack repo you want to download from.
PACKS_REPO_URL = 'https://packs.download.microchip.com/'


def should_get_this_pack(name: str) -> bool:
    ''' Return True if the given pack name appears to be for a device we want to support.

    For now, this will look for 32-bit ARM devices such as the SAM and PIC32C devices. You can edit
    this function if you want to download packs for other devices.
    '''
    return True


class PacksHtmlParser(HTMLParser):
    '''A super simple subclass of HTMLParser to look for download links for packs and put those into
    a list for later.

    This is based on the examples and docs for the 'html.parser' library found at
    https://docs.python.org/3/library/html.parser.html#module-html.parser. Have a look there to get
    a better idea of what this is doing. See the main code below to see how to use this class.
    '''
    def __init__(self):
        super().__init__()

        self.links: list[str] = []


    def get_pack_links(self):
        '''Return a list of links to file packs.

        The links are relative to the URL from which they were read. You need to feed the HTML data
        from the URL to this parser using the 'feed()' method first before this will return anything
        useful.
        '''
        return self.links


    def handle_starttag(self, tag, attrs):
        '''This is called by the HTMLParser superclass whenever a start tag is found.

        In our case, we want to look for download links for pack files, which end in '.atpack'.
        This will put links into a list that can be retrieved later from this instance.
        '''
        # The tags we're looking for look like this:
        #    <a href="Microchip.ATautomotive_DFP.3.1.73.atpack" download="">
        #
        # Look for the 'a' tag with the 'href' and 'download' attributes.
        #
        if 'a' == tag:
            href: str = ''
            download: bool = False

            for attr in attrs:
                if 'download' == attr[0]:
                    download = True
                elif 'href' == attr[0]  and  attr[1]  and  attr[1].endswith('.atpack'):
                    href = attr[1]

            if download:
                # We found a valid pack download link, so hold onto it.
                self.links.append(href)


if '__main__' == __name__:
    pack_links: list[str] = []

    with urllib.request.urlopen(PACKS_REPO_URL, data=None, timeout=10.0) as req:
        # Grab the HTML from the packs URL.
        html_data: str = req.read().decode('utf-8')

        # Create our custom HTML parser and pass the HTML to that.
        parser = PacksHtmlParser()
        parser.feed(html_data)
        parser.close()

        # Now that the parser has parsed the HTML, we can see what links to packs it has found.
        pack_links = parser.get_pack_links()
    
    for link in pack_links:
        print(link)
