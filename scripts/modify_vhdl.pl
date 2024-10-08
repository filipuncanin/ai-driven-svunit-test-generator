#!/usr/bin/env perl
use strict;
use warnings;

# Get the filename from the command line argument
my $filename = $ARGV[0];

# Open the file for reading and writing
open my $file, '+<', $filename or die "Could not open file '$filename': $!\n";

# Check if the file is already modified
my $modification_needed = 1; # Assume modification is needed
while (my $check_line = <$file>) {
    if ($check_line =~ /^\s*use\s+work\.pack\.all\s*;/i) {
        $modification_needed = 0;
        last;
    }
}

# Close file and exit if modification is not needed
unless ($modification_needed) {
    print "File is already modified. No need for further changes.\n";
    close $file;
    exit;
}

# Reset the file pointer to the beginning of the file
seek $file, 0, 0;

# Read the lines of the file into an array
my @lines = <$file>;

# Find the line with "entity"
my $entityLine;
for my $line (@lines) {
    if ($line =~ /^\s*entity/i) {
        $entityLine = $line;
        last;
    }
}

# Insert "use work.pack.all;\n\n" before the line with "entity"
for my $i (0..$#lines) {
    if (defined $entityLine and $lines[$i] =~ /^\Q$entityLine/) {
        splice @lines, $i, 0, "use work.pack.all;\n\n";
        last;
    }
}

# Find the lines starting with "type" and collect all lines until we reach ";"
my $typeBlock = "";
my $isTypeBlock = 0;

for my $line (@lines) {
    # If we encounter a "type" declaration, start collecting
    if ($line =~ /^\s*type/i) {
        $isTypeBlock = 1;
    }
    
    # If we are in a "type" block, keep appending lines until we hit a semicolon
    if ($isTypeBlock) {
        $typeBlock .= $line;
        if ($line =~ /;/) {
            $isTypeBlock = 0;
            last;  # Exit after collecting the full type block
        }
    }
}

# Create the "pack.vhd" file using the collected type block
if ($typeBlock) {
    open my $packFile, '>', 'pack.vhd' or die "Could not create file 'pack.vhd': $!\n";
    print $packFile "package pack is\n";
    print $packFile $typeBlock;
    print $packFile "end package;\n";
    close $packFile;
}

# Move the file pointer to the beginning of the file
seek $file, 0, 0;

# Add "--" in front of the type block in the original file
my $inTypeBlock = 0;

for my $i (0..$#lines) {
    if ($lines[$i] =~ /^\s*type/i) {
        $inTypeBlock = 1;
    }
    
    if ($inTypeBlock) {
        $lines[$i] = "--" . $lines[$i];
        if ($lines[$i] =~ /;/) {
            $inTypeBlock = 0;  # End the commenting after reaching the semicolon
            last;
        }
    }
}

# Write the modified lines back to the file
seek $file, 0, 0;
print $file @lines;

# Close the file
close $file;

############################
# Get a list of all *.vhd files in the current directory
my @vhd_files = glob("*.vhd");

# Find the index of "pack.vhd" in the list
my $pack_index = -1;
for my $i (0..$#vhd_files) {
    if ($vhd_files[$i] eq "pack.vhd") {
        $pack_index = $i;
        last;
    }
}

# If "pack.vhd" is found, move it to the beginning of the list
if ($pack_index >= 0) {
    my $pack_file = splice(@vhd_files, $pack_index, 1);
    unshift @vhd_files, $pack_file;
}

# Write the list of VHDL files to VHDLfiles.f
open my $vhdlist_file, '>', 'VHDLfiles.f' or die "Could not create file 'VHDLfiles.f': $!\n";
print $vhdlist_file join("\n", @vhd_files);
close $vhdlist_file;

print "Modification complete. Package file 'pack.vhd' created.\n";
