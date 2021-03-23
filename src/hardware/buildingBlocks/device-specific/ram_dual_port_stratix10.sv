//-----------------------------------------------------
// Design Name : Ram Dual Port
// Function    : Dual port ram for Intel for Stratix 10 FPGAs
//-----------------------------------------------------

module  ram_dual_port  (
    address_a,
    address_b,
    clk,
    data_a,
    data_b,
    wren_a,
    wren_b,
    q_a,
    q_b,
    clken,     //Never used
    byteena_a, //Never used
    byteena_b);//Never used


    parameter  width_a = 1'd0;
    parameter  width_b = 1'd0;
    parameter  widthad_a = 1'd0;
    parameter  widthad_b = 1'd0;
    parameter  numwords_a = 1'd0;
    parameter  numwords_b = 1'd0;
    parameter  latency = 1'd1;
    parameter  init_file = "UNUSED";
    parameter  width_be_a = 1'd0;
    parameter  width_be_b = 1'd0;

    input [(widthad_a-1):0] address_a;
    input [(widthad_b-1):0] address_b;
    input clk;
    input [(width_a-1):0] data_a;
    input [(width_b-1):0] data_b;
    input wren_a;
    input wren_b;
    output [(width_a-1):0] q_a;
    output [(width_b-1):0] q_b;
    input  clken;
    input  byteena_a;
    input  byteena_b;
    tri1     clk;
    tri0     wren_a;
    tri0     wren_b;
    reg  clk_wire;

    wire [(width_a-1):0] q_a_wire;
    wire [(width_b-1):0] q_b_wire;
    wire [(width_a-1):0] q_a = q_a_wire[(width_a-1):0];
    wire [(width_b-1):0] q_b = q_b_wire[(width_b-1):0];

    altera_syncram  altera_syncram_component (
                .address_a (address_a),
                .address_b (address_b),
                .clock0 (clk_wire),
                .data_a (data_a),
                .data_b (data_b),
                .wren_a (wren_a),
                .wren_b (wren_b),
                .q_a (q_a_wire),
                .q_b (q_b_wire),
                .aclr0 (1'b0),
                .aclr1 (1'b0),
                .address2_a (1'b1),
                .address2_b (1'b1),
                .addressstall_a (1'b0),
                .addressstall_b (1'b0),
                .byteena_a (1'b1),
                .byteena_b (1'b1),
                .clock1 (1'b1),
                .clocken0 (1'b1),
                .clocken1 (1'b1),
                .clocken2 (1'b1),
                .clocken3 (1'b1),
                .eccencbypass (1'b0),
                .eccencparity (8'b0),
                .eccstatus (),
                .rden_a (1'b1),
                .rden_b (1'b1),
                .sclr (1'b0));
    defparam

        altera_syncram_component.address_reg_b  = "CLOCK0",
        altera_syncram_component.clock_enable_input_a  = "BYPASS",
        altera_syncram_component.clock_enable_input_b  = "BYPASS",
        altera_syncram_component.clock_enable_output_a  = "BYPASS",
        altera_syncram_component.clock_enable_output_b  = "BYPASS",
        altera_syncram_component.indata_reg_b  = "CLOCK0",
        altera_syncram_component.init_file = init_file, //"STRING",
        altera_syncram_component.intended_device_family  = "Stratix 10",
        altera_syncram_component.lpm_type  = "altera_syncram", // This was "altsyncram"
        altera_syncram_component.numwords_a  = numwords_a,
        altera_syncram_component.numwords_b  = numwords_b,
        altera_syncram_component.operation_mode  = "BIDIR_DUAL_PORT",
        altera_syncram_component.outdata_aclr_a  = "NONE",
        altera_syncram_component.outdata_sclr_a  = "NONE",
        altera_syncram_component.outdata_aclr_b  = "NONE",
        altera_syncram_component.outdata_sclr_b  = "NONE",
        altera_syncram_component.outdata_reg_a  = "UNREGISTERED", 
        altera_syncram_component.outdata_reg_b  = "UNREGISTERED",
        altera_syncram_component.power_up_uninitialized  = "FALSE",
        altera_syncram_component.read_during_write_mode_mixed_ports  = "DONT_CARE", // This was "OLD_DATA"
        altera_syncram_component.read_during_write_mode_port_a  = "NEW_DATA_NO_NBE_READ",
        altera_syncram_component.read_during_write_mode_port_b  = "NEW_DATA_NO_NBE_READ",
        altera_syncram_component.widthad_a  = widthad_a,
        altera_syncram_component.widthad_b  = widthad_b,
        altera_syncram_component.width_a  = width_a,
        altera_syncram_component.width_b  = width_b,
        altera_syncram_component.width_byteena_a  = width_be_a, 
        altera_syncram_component.width_byteena_b  = width_be_b; 


  always @(*) begin
    clk_wire = clk;
  end


  integer j;
  reg [(width_a-1):0] q_a_reg[latency:1], q_b_reg[latency:1];

  always @(*)
  begin
     q_a_reg[1] <= q_a_wire;
     q_b_reg[1] <= q_b_wire;
  end

  always @(posedge clk)
  if (clken)
  begin
     for (j = 1; j < latency; j=j+1)
     begin
         q_a_reg[j+1] <= q_a_reg[j];
         q_b_reg[j+1] <= q_b_reg[j];
     end
  end

  assign q_a = (clken) ? q_a_reg[latency] : 0;
  assign q_b = (clken) ? q_b_reg[latency] : 0;

endmodule


