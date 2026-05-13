/**

APRILCUBE

3D-Model of an Aprilcube. Each side has a different april tag on it.
Used for easy object detection.

terminology:
"tags" refers to the black part of the apriltag that is printed as loos thin plates
"cube" refers to the solid cube and the white parts of the tags, that are printed onto the cube

 */


// Object Parameters (all length in mm)
cube_side_length = 50; // cube side
tag_height = 1; // tickness of the tags

// Rendering Parameters
tag_shape_offset = 0.3; // offset to connest disconnected pixels and print tags in one piece
tol_to_cube = 0.0; // tolerance taken away from the cube (only influences the cube)
tol_to_tag = 0.15; // tolerance taken away from the tags (only influences the tags), should be >0 and <tag_shape_offset (see comment at tolerance test below)
// total tolerance = tol_to_tag + tol_to_cube

// --- TAGS ---

module tag2D(index, r_off)
{
    // shortcuts
    l = cube_side_length;
    
    // generate file name
    file_name = str("svg/tag",str(index),".svg");
    
    // scaling
    dots_per_mm = 8; // initial size of imported tag (dots=pixels)
    mm_per_inch = 25.4; 
    dpi = dots_per_mm * mm_per_inch; // draws the tag in a 1x1 square
    
    offset(r_off)
    scale([l,l]) 
    import(file_name, center=true, dpi=dpi); 
}
//tag2D(index=1, r_off=tag_shape_offest);

module tagplate(index, tol)
{   
    r_off = tag_shape_offset + tol;
    h = tag_height + tol;
    
    translate([0,0,-h+1e-4])
    linear_extrude(h) tag2D(index, r_off);
}
module tag_pos(index) { tagplate(index, tol=-tol_to_tag); }
module tag_neg(index) { tagplate(index, tol=+tol_to_cube); }
//tag_pos(index=1);
//#tag_neg(index=0);


module tagplates(tol)
{
    // position and rotate tags to correct pose
    c = cube_side_length/2;
    
    rotate([  0,0,0]) translate([0,0,c]) tagplate(0, tol); // top
    rotate([180,0,0]) translate([0,0,c]) tagplate(5, tol); // bottom
    
    rotate([-90,0,0]) translate([0,0,c]) tagplate(2, tol); // left
    rotate([ 90,0,0]) translate([0,0,c]) tagplate(3, tol); // right
    
    rotate([0, 90,0]) translate([0,0,c]) tagplate(1, tol); // front
    rotate([0,-90,0]) translate([0,0,c]) tagplate(4, tol); // back
}
module tags_pos() { tagplates(tol=-tol_to_tag); }
module tags_neg() { tagplates(tol=+tol_to_cube); }
//tagplates(tol=-tol_to_tag);
//#tagplates(tol=tol_to_cube);



// -----------------------------------
// CUBE

module tagcube()
{
    // just the white insides of the cube, the negative of the tags are subtracted
    // print this in white
    
    l = cube_side_length;
    
    difference ()
    {
        cube([l,l,l],  center=true);
        tags_neg(); // negatives
    }
}
//tagcube();




// -------------------------------
// TOLERANCE TEST


module test_one_side(index)
{
    // only top face to test tolerance
    
    l = cube_side_length;
    h = tag_height;
    
    translate([0,0,h])
    {
        difference() 
        {
            cube([l, l, 2*h], center=true);
            translate([0,0,h]) tag_neg(index);
        }
        
        translate([1.1*l,0]) tag_pos(index);
    }
}
//test_one_side(1);

module toltest_plates()
{
    l = cube_side_length;
    h = tag_height;
    
    index = 1;
    step = tag_shape_offset/6;
    t2ts = [ // list of tol_to_tags
        for (t=[0:step:tag_shape_offset-step]) t
    ];
    echo(t2ts);
    
    union() for (i=[0:len(t2ts)-1])
    {
        x = 1 * l * (len(t2ts)/2-i-0.5);
        t = t2ts[i];
        o = tag_shape_offset-t;
        
        translate([x,0,0])
        {
            
            ht = h-t;
            rotate([0,180,0]) tagplate(index, tol=-t);
            linear_extrude(0.4+ht){
                rotate(90)translate([3*l/9,3*l/9]) text(
                    str("tol=",str(t)),
                    font="FreeSans:style=Bold",
                    size=l / 14,
                    halign="right",
                    valign="top"
                );
                translate([3*l/9,3*l/9]) text(
                    str("off=",str(o)),
                    font="FreeSans:style=Bold",
                    size=l / 14,
                    halign="right",
                    valign="top"
                );
            }
        }
    }
}
toltest_plates();
/**
 * Test
 *  - Printer: Bamboo Lab X1
    - Nozzel: 0.4mm
    - Filament: PLA
    - Bed: Texture PEI
    - Layer: 0.2mm

    Results:
    - tol=0.2 good
    - tol=0.15 tight with force
 */


// ---------------------------------
// LAYOUT

module tagplates_layout()  
{
    // layout tags ready to print
    t=tag_height;    
    off=tag_shape_offset;
    c = 1.1 * cube_side_length;
    rotate([180,0,0])
    {
        translate([ c, c,0]) tag_pos(0); // top
        translate([-c,-c,0]) tag_pos(5); // bottom
        
        translate([0,c,0]) tag_pos(2); // left
        translate([0,-c,0]) tag_pos(3); // right
        
        translate([c,0,0]) tag_pos(1); // front
        translate([-c,0,0]) tag_pos(4); // back
    }
}
//color("black") tags_layout();
//color("white") translate([0,0,cube_side_length/2]) tagcube();


// -------------------------------
// RENDERING

module fullcube()
{
    // fully assemble cube with all tags at the intended spot
    color("white") tagcube();
    color("black") tags_pos();
}
//fullcube();

























































// scroll past end