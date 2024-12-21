## Usage

If no CLI arguments are provided, a nice Qt GUI will ask user for `-i` and `-o`

### gpx2map

creates html zoomable map with all routes from gpx activites highlighted with a nice blue color

`-i` `--input` input directory with gpxfiles
`-o` `--output` output name, html result will be stored in parent directory of `-i`

### gpx2csv

creates csv file with km/h speed and min/km pace for each minute of the active, and a simple png plot of that speed across time

`-i` `--input` input gpx file
`-o` `--output` output name, csv and png results will be stored in parent directory of `-i`