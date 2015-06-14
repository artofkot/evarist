    pybabel extract -F babel.cfg -o messages.pot .      #generates .pot filr
    pybabel update -i messages.pot -d translations      #updates .po file according to .pot file
    pybabel compile -d translations                     #generates translations


    BE CAREFULL WITH THIS! You want to use only once to generate messages.po file, and then only update it by second script
    pybabel init -i messages.pot -d translations -l en  #sends strings to .po file, then write translations there