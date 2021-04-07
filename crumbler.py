'''
Converts a directory of markdown files to html, including subdirectories.
Navigation breadcrumbs will be generated for directories that contain a file
with the same name as the directory (e.g. dirname.md) either in that directory
or in their shared parent directory, or if the directory contains an index.md
file.

Arguments:
-b, --breadcrumb: A path to a file containing a template used for the breadcrumbs.
-c, --css: A path to a CSS file to reference in the html's head.
-d, --dirout: The name of the directory used for the output.
-h, --html: A path to a file containing a template for the overall html file.
-j, --js: A path to a Javascript file to reference in the html's head.
-l, --local: If included, will generate file paths for the local file system. If excluded, will generate file paths as web URIs.
-p, --path: The path to the parent directory of the markdown files.
-t, --title: A default title to give to pages if a topmost header (<h1>) cannot be found.
-w, --webpath: The default base path for web URIs.
'''
import markdown, os, re, sys
from bs4 import BeautifulSoup as bs
from shutil import copy

ARGV_SHORTCUTS = {
    'b': 'breadcrumb',
    'c': 'css',
    'd': 'dirout',
    'h': 'html',
    'j': 'js',
    'l': 'local',
    'p': 'path',
    't': 'title',
    'w': 'webpath',
}

BOILERPLATE = r'''
<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  {style}
  {script}

</head>

<body>
    <nav class="breadcrumbs">
        <ul>
            {breadcrumbs}
        </ul>
    </nav>
    <div class="page">
        <nav class="toc">
            {toc}
        </nav>
        <section class="main">
            {body}
        </section>
    </div>
</body>
</html>
'''

BREADCRUMB = r'''
<li>
  <a href="{href}">{text}</a>
</li>
'''

CSS_TAG = '<link rel="stylesheet" href="{css}">'

DEFAULT_ARGS = {
    'breadcrumb': '',
    'css': [],
    'dirout': 'build',
    'html': '',
    'js': [],
    'local': False,
    'path': os.path.join('.', ''),
    'title': None,
    'webpath': '',
}

JS_TAG = '<script src="{js}" type="application/javascript">'


class Breadcrumb:
    '''
    A breadcrumb used to construct page navigation
    '''
    path = None
    md_file = None
    html_file = None
    text = ''
    html = ''

    def __init__(
        self,
        root=os.path.join('.', ''),
        path='',
        text='',
        html_template='',
        start_path=None,
        is_local=False,
        webroot=''):
        path = slash_trim(path)
        root = slash_trim(root)
        base = os.path.basename(path) if path else os.path.basename(root)
        crumb_path = Breadcrumb._get_crumb(path, root, base, start_path, is_local, webroot)
        if crumb_path is not None:
            crumb_path = slash_trim(crumb_path)
            self.path = path
            self.md_file = crumb_path
            self.html_file = f'{crumb_path[:-3]}.html'
            if not text:
                text = base.replace('_', ' ').title()
            self.text = text
            self.html = html_template.format(href=self.html_file, text=text)
    
    def exists(self):
        '''
        Returns True if the Breacrumb has an html string else False.
        '''
        return len(self.html) > 0

    @staticmethod
    def _get_crumb(path, root=os.path.join('.', ''), base=None, start=None, is_local=False, webroot=''):
        '''
        Checks if path/base.md or path/index.md exists and 
        returns the name of the found file. Returns `None`
        if neither is found.
        If `base` is not provided, it uses the name of the
        top-most directory in the path.
        '''
        root = slash_trim(root)
        path = slash_trim(path)
        path = os.path.join(root, path)
        if base is None:
            base = os.path.basename(path)
        file_base = f'{base}.md'
        crumb_path = os.path.join(path, file_base)
        if os.path.exists(crumb_path):
            if is_local:
                if start:
                    return os.path.relpath(crumb_path, start)
                return crumb_path[len(root):]
            return get_url_path(crumb_path, '', root, webroot)
        crumb_path = os.path.join(path, 'index.md')
        if os.path.exists(crumb_path):
            if is_local:
                if start:
                    return os.path.relpath(crumb_path, start)
                return crumb_path[len(root):]
            return get_url_path(crumb_path, '', root, webroot)
        crumb_path = os.path.join(
            '.',
            os.path.relpath(os.path.join(path, os.pardir)),
            file_base)
        if os.path.exists(crumb_path):
            if is_local:
                if start:
                    return os.path.relpath(crumb_path, start)
                return crumb_path[len(root) + 1:]
            return get_url_path(crumb_path, '', root, webroot)
        return 

class DocFragment:
    md_converter = markdown.Markdown(tab_length=2, extensions=['toc'])
    default_parser = 'html.parser'

    def __init__(
            self,
            breadcrumbs='',
            file_name=None,
            fragment=None,
            is_local=False,
            md=None,
            parser=None,
            path='',
            path_out=os.path.join('.', 'html_out', ''),
            root=os.path.join('.', ''),
            script_tag=None,
            style_tag=None,
            template=BOILERPLATE,
            webroot=''):
        self.breadcrumbs = breadcrumbs
        self.fragment = fragment
        self.file_name = file_name
        self.is_local = is_local
        self.md = md
        self.parser = parser if parser is not None else DocFragment.default_parser
        self.path = path
        self.path_out = path_out
        self.root = root
        self.script_tag = script_tag
        self.soup = None
        self.style_tag = style_tag
        self.template = template
        self.title = None
        self.webroot = webroot

    def convert_md_to_html(self):
        if self.md is None:
            self.read_file()
        if self.md is None:
            raise "No fragment contents found."
        self.fragment = DocFragment.md_converter.convert(self.md)
        return self.fragment

    def fix_html(self):
        self.fix_links()
        self.fix_imgs()
        return self.fragment

    def fix_imgs(self):
        if self.soup is None:
            self.make_soup()
        for img in self.soup.select('img'):
            src = img.get('src')
            if not self.is_local:
                src = get_url_path(src, self.path, self.root, self.webroot)
            img['src'] = src
        self.fragment = str(self.soup)
        return self.fragment

    def fix_links(self):
        if self.soup is None:
            self.make_soup()
        is_xlink = False
        for link in self.soup.select('a'):
            href = link.get('href')
            if not href:
                href = link.get('xlink:href')
                is_xlink = True
            if not re.match(r'{.*}', href):
                if not self.is_local:
                    href = get_url_path(href, self.path, self.root, self.webroot)
                href = re.sub(r'\.md(?:\b|$)', '.html', href)
                if is_xlink:
                    link['xlink:href'] = href
                else:
                    link['href'] = href
        self.fragment = str(self.soup)
        return self.fragment

    def find_title(self, default=None):
        if self.soup is None:
            self.make_soup()
        h1 = self.soup.h1
        if h1 is not None:
            self.title = h1.get_text()
        elif default is not None:
            self.title = default
        else:
            self.title = os.path.splitext(os.path.basename(self.file_name))[0]
        return self.title

    def make_soup(self):
        if self.fragment is None:
            if self.file_name is not None and self.md is None:
                self.read_file()
            if self.md is not None:
                self.convert_md_to_html()
        self.soup = bs(self.fragment, self.parser)
        return self.soup
    
    def read_file(self):
        file_path = os.path.join(self.path, self.file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            ext = os.path.splitext(file_path)[1]
            if ext == ".md":
                self.md = f.read()
            else:
                self.fragment = f.read()

    def write_file(
            self,
            breadcrumbs=None,
            fragment=None,
            script_tag=None,
            style_tag=None,
            template=None,
            title=None):
        if self.file_name[-3:] == '.md':
            file_path_out = os.path.join(
                self.path_out,
                f'{os.path.splitext(os.path.basename(self.file_name))[0]}.html')
        else:
            file_path_out = os.path.join(
                self.path_out,
                self.file_name)
        with open(file_path_out, 'w+', encoding='utf-8') as f_out:
            if fragment is None:
                if self.fragment is None:
                    fragment = str(self.make_soup())
                else:
                    fragment = self.fragment
            breadcrumbs = breadcrumbs if breadcrumbs is not None else self.breadcrumbs
            script_tag = script_tag if script_tag is not None else self.script_tag
            style_tag = style_tag if style_tag is not None else self.style_tag
            template = template if template is not None else self.template
            if title is None:
                if self.title is None:
                    title = self.find_title()
                else:
                    title = self.title
            html_contents = template.format(
                title=title,
                breadcrumbs=breadcrumbs,
                body=fragment,
                script=script_tag,
                style=style_tag,
                toc=DocFragment.md_converter.toc)
            f_out.truncate()
            f_out.write(html_contents)


def get_breadcrumbs(
        root=os.path.join('.', ''),
        path='',
        start_path='',
        template=BREADCRUMB,
        is_local=False,
        webroot=''):
    crumbs = []
    path = slash_trim(path).split(os.path.sep)
    if ''.join(path):
        for i in range(len(path) + 1):
            crumb = Breadcrumb(
                root=root,
                path=os.path.join(*path[:i]) if i else '',
                html_template=template,
                start_path=start_path,
                is_local=is_local,
                webroot=webroot)
            if crumb.exists():
                crumbs.append(crumb)
    else:
        crumbs = [Breadcrumb(
            root=root,
            path='',
            html_template=template,
            start_path=start_path,
            is_local=is_local,
            webroot=webroot)]
    return crumbs

def get_file_from_sys_args(root, name, args, default):
    filename = os.path.join(root, args.get(name)) if args.get(name) else None
    contents = default
    if filename:
        with open(filename) as file_in:
            contents = file_in.read()
    return contents


def get_url_path(link, path, root, webroot):
    link = link.replace('file:///', '')
    link_path = os.path.abspath(os.path.join(path, link))
    root_path = os.path.abspath(root)
    url = os.path.relpath(link_path, root_path)
    url = os.path.join(webroot, url)
    url = url.replace('\\', '/')
    if not re.match('^/', url):
        url = f'/{url}'
    return url


def parse_sys_args():
    args = {
        'css': [],
        'js': [],
    }
    next_key = None
    try:
        for i in range(1, len(sys.argv)):
            key = None
            if sys.argv[i][:2] == '--':
                if sys.argv[i][2:] == 'help':
                    print(__doc__)
                    exit()
                else:
                    key = sys.argv[i][2:]
            elif re.match(r'-\w$', sys.argv[i]):
                key = ARGV_SHORTCUTS[sys.argv[i][1]]
            elif next_key is not None:
                if next_key in ['css', 'js']:
                    args[next_key].append(sys.argv[i])
                elif next_key in DEFAULT_ARGS:
                    if key is not None or not sys.argv[i]:
                        print(f'{__doc__}\nError - {key} must be followed by an argument')
                        exit(1)
                    args[next_key] = sys.argv[i]
                    next_key = None
            if key in DEFAULT_ARGS:
                next_key = None
                if key == 'local':
                    args[key] = True
                else:
                    next_key = key
            elif key:
                print(f'{__doc__}\nError - Unknown argument: {sys.argv[i]}')
                exit(1)
    except:
        print('Unknown error parsing system arguments.')
        exit(1)
    return args


def slash_trim(s):
    return re.sub(f'^\\{os.path.sep}|\\{os.path.sep}$', '', s)


# TODO: Site ToC/map
# TODO: rebuild with pathlib

sys_args = parse_sys_args()

for key in DEFAULT_ARGS:
    if key not in sys_args:
        sys_args[key] = DEFAULT_ARGS[key]

root = sys_args.get('path')
webroot = sys_args.get('webpath')
is_local = sys_args.get('local')

base_out = os.path.join(root, sys_args.get('dirout'))

html_template = DocFragment(
    fragment=get_file_from_sys_args(root, 'html', sys_args, BOILERPLATE),
    path='',
    root=root,
    is_local=is_local,
    webroot=webroot,
)
html_template.fix_html()

breadcrumb_template = DocFragment(
    fragment=get_file_from_sys_args(root, 'breadcrumb', sys_args, BREADCRUMB),
    path='',
    root=root,
    is_local=is_local,
    webroot=webroot,
)
breadcrumb_template.fix_html()

css = sys_args.get('css')
style = '\n'.join([CSS_TAG.format(css=_) for _ in css])

js = sys_args.get('js')
script = '\n'.join([JS_TAG.format(js=_) for _ in js])

prog = 0

for rt, dr, fn in os.walk(root):
    rt_out = os.path.join(
        base_out,
        slash_trim(rt[len(root):]))
    prog = (prog + 1) % 20
    print(f''.join([' '] * (0 if prog <= 10 else prog - 10)) +
        ''.join(['.'] * (prog if prog <= 10 else 20 - prog)) + 
        ''.join([' '] * (10 - prog if prog <= 10 else 0)), end='\r')
    if rt[:len(base_out)] != base_out:
        os.makedirs(rt_out, exist_ok=True)
        breadcrumbs = '\n'.join([_.html for _ in get_breadcrumbs(
            root=root,
            path=rt[len(root):],
            start_path=rt,
            template=breadcrumb_template.fragment,
            is_local=is_local,
            webroot=webroot)])
        for file_name in fn:
            try:
                if '.md' == file_name[-3:] or '.svg' == file_name[-4:]:
                    if '.svg' == file_name[-4:]:
                        parser = 'xml'
                        template = '{body}'
                    else:
                        parser = DocFragment.default_parser
                        template = html_template.fragment
                    fragment = DocFragment(
                        breadcrumbs=breadcrumbs,
                        file_name=file_name,
                        is_local=is_local,
                        parser=parser,
                        path=rt,
                        path_out=rt_out,
                        root=root,
                        script_tag=script,
                        style_tag=style,
                        template=template,
                        webroot=webroot)
                    fragment.find_title(sys_args.get('title'))
                    fragment.fix_html()
                    fragment.write_file()
                    
                elif not os.path.samefile(
                        os.path.join(rt, file_name),
                        __file__) \
                    and not os.path.samefile(
                        os.path.join(rt, file_name),
                        os.path.join(root, sys_args.get('html', ''))) \
                        and not os.path.samefile(
                            os.path.join(rt, file_name),
                            os.path.join(root, sys_args.get('breadcrumb', ''))):
                    copy(os.path.join(rt, file_name), rt_out)
            except:
                print(f'ERROR - Could not convert or transfer file: {os.path.join(rt, file_name)}')
print('\rDone!     ')