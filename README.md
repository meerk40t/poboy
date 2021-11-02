# poboy
POboy is a free and easy po editor and maintainer

Poboy is a translation editor and maintenance program. We seek to solve two problems. First, providing a high quality easy to use PO file editor. And second by providing tools to help maintain and update changing python code translations by generating new template files and providing tools with regard to the differences found with those files.

Typically with regard to translations:
* We have an up-to-date source code that can be used to generate a PO template.
* We have a no translations or potentially outdated translations from older versions of the software.

With so if we have a freshly generated template for our po file (since we have the source and can generate this) what we need is the ability to not merely edit the PO but also to compare that file to the current version of what the template *should be*. This provides us two bits of potentially extremely helpful information.

* A list of the `msgid` which were not translated because they did not exist. (New Entries)
* A list of the `msgid` which were translated but which no longer exist. (Orphans)

By comparing these we can find new high-priority strings which were not translated but should be translated, and we find previously translated strings which no longer match anything found in the source code.

This provides us with tools that are not availible to others, namely the ability to update and maintain the PO files in ways which respect the time of the translators. And allows us to have fine grain control over the update of our po files.

## Origins

This file is a result of some work with MeerK40t and a desire to provide a built in PO editor within the program. While understanding that this is well outside the scope of laser cutting software, the use of wxPython within that program and tools such as pybabel. The most likely volunteers for providing translations are the people currently using the program. And po editors are not complex programs. They are a thin layer of text editor with tools to facilitate fast work by translators, and a considerable amount of i18n understanding and know how.

While this was originally written for use within that program it became quickly clear that this program work would benefit other especially since a reduce set of the same features would still result in a very nice PO file editor. So there is considerable utility to this as a standalone program. Also, with the MeerK40t plugin system there is no actual need for this program to be directly included into the larger source.

It also became quite clear that the needed functionality for the message extraction and catalog reading was well done within the `babel` project however directly including this as a requirement would also require `pytz` as a requirement and nothing about the messages functionality depended on that code. So there is a hard fork at python-babel/2.9.1 of the messages code. And edits made to just this part of the functionality.


## Goals

While the current goal is to work for the original purpose considerable work will go into making this work generic po-editing applications. This should be considered a stand-alone application but the feature set will be strongly geared towards it's use within MeerK40t.

## Philosophy

We will not dive too deeply into the highly specific work of the very fine details, but providing the broader strokes of giving the users methods for dealing with these details.

We will do everything we can to help make this and our own job easier.

## Acknowledgments

The bablemsg package is hard forked from https://github.com/python-babel/babel


```
Copyright (c) 2013-2021 by the Babel Team, see AUTHORS for more information.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
 3. The name of the author may not be used to endorse or promote
    products derived from this software without specific prior
    written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

