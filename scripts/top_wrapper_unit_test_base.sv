import pack::*;

`include "svunit_defines.svh"
`include "top_wrapper.sv"

module top_wrapper_unit_test;
  	import svunit_pkg::svunit_testcase;

  	string name = "top_wrapper_ut";
  	svunit_testcase svunit_ut;

	tstate sSTATE, sNEXT_STATE;

	localparam iCLK_period = 10;

	function void build();
		svunit_ut = new(name);
	endfunction

	task setup();
		svunit_ut.setup();
	endtask

	task teardown();
 		svunit_ut.teardown();
  	endtask
      
    initial begin
		$assertvacuousoff(0);
		iCLK = 0;

		forever begin
			#5 iCLK = ~iCLK;
		end
	end

  	`SVUNIT_TESTS_BEGIN
		`SVTEST(TESTIRANJE_SIGNALA_DUT)

		`SVTEST_END
  	`SVUNIT_TESTS_END

endmodule


