[out:json][timeout:30000];
area["name:en"="Nagoya"]->.outer;
area["name:en"="Naka Ward"]->.inner;
(
  nwr["building"="church"](area.inner)(area.outer);
);
out geom;
