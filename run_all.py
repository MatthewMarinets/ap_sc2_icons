
import clean_icons
import convert
import generate_html
import parse_icon_data

if __name__ == '__main__':
    FAST = True
    parse_icon_data.main()
    if not FAST: clean_icons.main()
    convert.main(FAST)
    generate_html.main()
