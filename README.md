# SublimeUrlConverter

A Sublime Text 3 package which converts raw urls to html/markdown links. Titles of links are fetched through target web pages.


## Supported formats

- HTML
- Markdown
- Custom format

### HTML

![Screenshot for html](https://raw.github.com/gh640/SublimeUrlConverter/master/assets/demo_html.gif)

### Markdown

![Screenshot for markdown](https://raw.github.com/gh640/SublimeUrlConverter/master/assets/demo_markdown.gif)

### Custom

![Screenshot for custom format](https://raw.github.com/gh640/SublimeUrlConverter/master/assets/demo_custom.gif)


## Usage

### Commands

You can run bulk url conversion with the following commands.

- `UrlConverter: Convert urls to html links`
- `UrlConverter: Convert urls to markdown links`
- `UrlConverter: Convert urls to custom-formatted links`

Select urls, open the command palette, and select one of the above commands.

### Settings

You can use a custom link format for the command. The default format is as shown below.

```json
{
  "fallback_template": "{title}\n{url}"
}
```

There are 2 tokens which can be used in the template: `{title}` and `{url}`.


## License

Licensed under the MIT license.
