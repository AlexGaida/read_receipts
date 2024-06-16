# read_receipts
Part of the Stanford's Code In Place Project, using easyocr module to parse receipt images and write them to files.
both .JSON and .CSV files are created

## info
.JSON cache file is created to verify existing files and to skip the ocr read because it takes a long time to parse each receipt.

I've included the generated .JSON and .CSV file for your inspection. Otherwise you may delete those if you want to see the code 
perform in action.

The tool will automatically should detect new receipts inside the folder.