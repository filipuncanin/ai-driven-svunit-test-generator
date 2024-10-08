#!/usr/bin/env perl
use strict;
use warnings;

# Define the HDL_PORT class
package HDL_PORT;
sub new {
    my ($class, $name, $direction, $type, $width) = @_;
    my $self = {
        PORT_NAME      => $name,
        PORT_DIRECTION => $direction,
        PORT_TYPE      => $type,
        PORT_WIDTH     => $width,
    };
    bless $self, $class;
    return $self;
}

# Get the filename from the command line argument
my $filename = $ARGV[0];

# Open the file for reading
open my $file, '<', $filename or die "Could not open file '$filename': $!\n";

# Read the lines of the file into an array
my @vhdl_lines = <$file>;

# Define an array to store HDL_PORT objects
my @hdl_ports;

# Recognize VHDL entity name
my ($hdl_entity) = grep(/^\s*entity\s+(\w+)\s+is/i, @vhdl_lines);
$hdl_entity =~ s/^\s*entity\s+(\w+)\s+is.*$/$1/i;
die "Error: Entity not found in VHDL file\n" unless defined $hdl_entity;
chomp $hdl_entity;

my $hdl_entity_inst = "${hdl_entity}_inst";

# Process each line to recognize ports
foreach my $line (@vhdl_lines) {
    if ($line =~ /^\s*(\w+)\s*:\s*(in|out|inout)\s*(std_logic|std_logic_vector)(?:\s*\(\s*(\d+)\s*downto\s*\d+\s*\))?\s*(?:;|\)|$)/i)
	{
        my $port_name      = $1;
        my $port_direction = $2;
        my $port_type      = $3;
        my $port_width     = ($port_type eq 'std_logic_vector') ? $4 + 1 : 1; #cuva pravu sirinu porta

        # Create an HDL_PORT object and push it to the array
        my $hdl_port = HDL_PORT->new($port_name, $port_direction, $port_type, $port_width);
        push @hdl_ports, $hdl_port;
    }
}

# Close the file
close $file;

# Display the results
print "VHDL Entity: $hdl_entity\n";
my $num_ports = scalar @hdl_ports;
print "Number of Ports Recognized: $num_ports\n";
foreach my $port (@hdl_ports) {
    printf "Port: %s, Direction: %s, Type: %s, Width: %d\n",
      $port->{PORT_NAME}, $port->{PORT_DIRECTION}, $port->{PORT_TYPE}, $port->{PORT_WIDTH};
}

# Open a new file for writing the Verilog wrapper
open my $verilog_file, '>', "${hdl_entity}_wrapper.sv" or die "Could not create file '${hdl_entity}_wrapper.sv': $!\n";

# Write Verilog module declaration
print $verilog_file "\n module ${hdl_entity}_wrapper (\n";
foreach my $i (0..$#hdl_ports) {
    my $port = $hdl_ports[$i];
    my $verilog_direction = ($port->{PORT_DIRECTION} eq 'in') ? 'input' : 'output';
    my $width_suffix = ($port->{PORT_WIDTH} > 1) ? "[" . ($port->{PORT_WIDTH} - 1) . ":0]" : "";
    
    # Use a conditional operator to handle the last comma
    my $comma = ($i == $#hdl_ports) ? "" : ",";
    printf $verilog_file "  %s %s %s%s\n", $verilog_direction, $width_suffix, $port->{PORT_NAME}, $comma;
}
print $verilog_file ");\n\n";


# Write Verilog instantiation of DUT
print $verilog_file "  // Instantiate design for testing $hdl_entity\n";
print $verilog_file "   $hdl_entity $hdl_entity_inst (\n";
foreach my $i (0..$#hdl_ports) {
    my $port = $hdl_ports[$i];
	# Use a conditional operator to handle the last comma
    my $comma = ($i == $#hdl_ports) ? "" : ",";
    printf $verilog_file "    .%s(%s)%s\n", $port->{PORT_NAME}, $port->{PORT_NAME},$comma;
}
print $verilog_file "  );\n\n";

# Write Verilog endmodule
print $verilog_file "endmodule\n";

# Close the Verilog file
close $verilog_file;

sub create_top_tb_wrapper {
    # Define the content to write to the file
    my $content = <<'END_CONTENT';
module top_tb_wrapper ();

    // Instantiate design for testing tb
    top_tb top_tb_inst ();

endmodule
END_CONTENT

    # Create and write to the file
    open my $file, '>', 'top_tb_wrapper.sv' or die "Could not open file: $!";
    print $file $content;
    close $file;
}

# Call the function to execute
create_top_tb_wrapper();


print "Verilog Wrapper File '${hdl_entity}_wrapper.sv' created.\n";
