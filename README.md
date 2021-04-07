# Markdown Crumbler
A markdown-to-html converter with directory-based breadcrumb navigation, base-plate template handling, and per-element src/href updates.

## Set-up

The Markdown Crumbler was built with [Python](https://www.python.org/) v3.8, [Python-Markdown](https://python-markdown.github.io/),  and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

### 1. Install Python

You can download the Python installer straight from their site at [https://www.python.org/]. For a more complete discussion of installing Python, see [this guide](https://wiki.python.org/moin/BeginnersGuide/Download).

Next, open the command line and check the instillation of Python by checking its version with this command:

```
python --version
```

It should return something like:
```
Python 3.8.5
```

If it returns `Python 2.x`, you may have more than one version of Python installed. That's alright. Try instead:

```
python3 --version
```

If that returns `Python 3.x`, use `python3` in place of `python` and `pip3` in place of `pip` in the commands below.

### 2. Getting the Markdown Crumbler Code

Next, you want to get the code for Markdown Crumbler. You can do that by cloning the GitHub repository here. You can download the files directly from [https://github.com/carteredge/markdown-crumbler], or if you have git installed, you can navigate to the parent directory you want the repository saved in and run the command:

```
git clone https://github.com/carteredge/markdown-crumbler.git
```

### 3. Setting up a Virtual Environment (Optional)

I recommend setting up a virtual environment for running Markdown Crumbler. This isn't required, especially as I attempted to keep external dependencies for the script to a miminum. It also adds an extra step whenever you run it (although, if you're like me, you'll want to set up a script file to do that for you).

That said, it keeps your global Python environment clean, which in simple terms means that if you want to run any other projects in Python, you won't have to worry about them installing something that conflicts with something used by Markdown Crumbler (especially if you also run *them* with a virtual environment).

There are lots of ways to create and run virtual environments for Python, but for this, the built-in `venv` will suffice.

In the command line terminal, navigate to the directory where you saved the Markdown Crumbler code and run:

```
python -m venv venv
```

This will create a virtual environment simply named `venv`.

Next, you will need to activate the virtual environment in the command line terminal before installing the Markdown Crumbler dependencies or running the Crumbler. (Once you have activated the virtual environment, it will stay activated in that terminal until you `deactivate` it or close the terminal window.

Activate the virtual environment with one of the following.

For Windows:

```
venv\scripts\activate
```

For Linux/Mac:

```
. venv/bin/activate
```

### 4. Installing Dependencies

Next, you'll want to install the dependencies required by Markdown Crumbler. Run the command:

```
pip install -r requirements.txt
```

### 5. Verify Installation

To quickly verify that Markdown Crumbler and its requirements are installed, you can run:

```
python crumbler.py --help
```

## Usage

To use the Markdown Crumbler, all you really need to do is use a command line terminal to navigat to the topmost directory of the Markdown files you wish to convert to HTML and run:

```
python crumbler.py
```

This will convert all of your Markdown files in the current directory into HTML files, generating a basic header with breadcrumb navigation and replacing any `<a>` href paths to Markdown files (currently only for HTML and SVG files). Additionally, Markdown Crumbler facilitates injecting CSS and JS references and other baseplate HTML into the converted markdown files. For more information on the HTML template, see the options below, particularly the HTML Template argument.

### Breadcrumbs

Breadcrumbs are added for directories if there is a file that meets one of the following criteria:

- A file in the same parent directory as the directory with the same name as the directory + `.md`
- A file in the directory with the same name as the directory + `.md`
- A file in the directory named `index.md`

The breadcrumb will link to that file, and all files in the directory and its subdirectories will have the breadcrumb added to their navigation.

## Options

Command line arguments can be used to provide external templates or select other options. As an example, if you wanted to provide HTML templates for the breadcrumbs called `bc.html` and for the page on a whole called `template.html` in addition to inserting a link to a CSS file at `/css/styles.css`, you would use the following command:

```
python crumbler.py -b bc.html -h template.html -c /css/styles.css
```

The available command line options are as follows:

### Breadcrumb Template

**Option**

`-b` or `--breadcrumb` followed by a path to a file containing an HTML template to use a custom template for your breadcrumb navigation entries. 

The custom template must include `{href}` where you want the link from the breadcrumb included, and `{text}` where you want the text label of the breadcrumb link.

**Default**

```html
<li>
  <a href="{href}">{text}</a>
</li>
```

### CSS

**Option**

`-c` or `--css` followed by a path to the CSS file. You can include multiple arguments for paths to different CSS files after the option, separated by spaces, e.g.:

```
python crumbler.py -c /css/styles.css https://some-external-site.com/more-styles.css
```

**Default**

None.  (I may include a default CSS file for future releases.)

### Output Directory Name

**Option**

`-d` or `--dirout` followed by the path or name of a directory to be used for output.

***Note:*** Files already in this directory will be ignored by the converter. Additionally, any files that match the name of files output by the converter will be overwritten.

**Default**

`build`

### HTML Template

**Option**

`-h` or `--html` followed by a path to a file containing a template for the overall html file.

The following template variables are used to insert various parts of the output (wrapped by curly brackets):

***title***  
The title tag of the document. Currently, Markdown Crumbler uses the first `h1` heading as the title of the page. If it does not find an `h1` element, it falls back on a default title provided via the `--title` or `-t` command line argument described below.

***breadcrumbs***  
The location where the generated breadcrumb code will be inserted.

***body***  
The location where the body of the document (i.e. the HTML generated from converting each Markdown document) will be inserted.

***script***  
The location of any `<script>` tags generated from `--js` or `-j` arguments.

***style***  
The location of any stylesheet `<link>` tags generated from `--css` or `-c` arguments.

***toc***  
The location of the Table of Contents generated from the page's headers. (This Table of Contents is provided by default, but in future releases will have options for its presence and behavior.)

**Default**

```html
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
```

### JavaScript File

**Option**

`-j` or `--js` followed by a path to a JavaScript file to reference in the HTML's `head`. You can include multiple arguments for paths to different JavaScript files after the option, separated by spaces, e.g.:

```
python /scripts/code.js /scripts/other-code.js
```

**Default**

None.

### Use Local Paths

**Option**

`-l` or `--local`  
If included, Markdown Crumbler will generate paths for `href` and `src` attributes (including the breadcrumbs) based off of relative local paths.

**Default**

Paths are generated as web URIs.

### Initial Path

**Option**

`-p` or `--path` followed by the path to the parent directory of the Markdown files where the Markdown Crumbler should start.

**Default**

The current working directory when `crumbler.py` is run.

### Default Title

**Option**

`-t` or `--title` followed by a default title to give to pages if a topmost header (`<h1>`) cannot be found.

**Default**

None.

### Web Path Root

**Option**

`-w` or `--webpath` followed by the default base path for URIs. For instance, if you wanted to use Markdown Crumbler to convert the docs of a project and planned to export them to a relevant `/docs/` path, you could use the command:

```
python crumbler.py -w /docs/
```

**Default**

`/`