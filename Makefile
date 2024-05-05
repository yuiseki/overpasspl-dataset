
church:
	python3 src/find_orphan_trident.py "data/concerns/building/church" | xargs -I{} python3 src/generate_overpassql.py "{}"

hotel:
	python3 src/find_orphan_trident.py "data/concerns/tourism/hotel" | xargs -I{} python3 src/generate_overpassql.py "{}"

gallery:
	python3 src/find_orphan_trident.py "data/concerns/tourism/gallery" | xargs -I{} python3 src/generate_overpassql.py "{}"

museum:
	python3 src/find_orphan_trident.py "data/concerns/tourism/museum" | xargs -I{} python3 src/generate_overpassql.py "{}"
