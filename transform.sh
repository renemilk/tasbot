#!/bin/bash
for i in modules static sources ; do 
	sed -i "s/_${i}/${i}/g" *.html
	mv _${i}/* ${i}/
	git add ${i}
done
