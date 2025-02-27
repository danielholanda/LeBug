//-----------------------------------------------------
// Design Name : Ram Dual Port
// Function    : Dual port ram for Intel for Cyclone V FPGAs
//-----------------------------------------------------

module ram_dual_port
(
  clk,
  clken,
  address_a,
  address_b,
  q_a,
  q_b,
  wren_a,
  wren_b,
  data_a,
  data_b,
  byteena_a,
  byteena_b
);

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

input  clk;
input  clken;
input [(widthad_a-1):0] address_a;
input [(widthad_b-1):0] address_b;
output [(width_a-1):0] q_a;
output [(width_b-1):0] q_b;
input  wren_a;
input  wren_b;
input [(width_a-1):0] data_a;
input [(width_b-1):0] data_b;
input [width_be_a-1:0] byteena_a;
input [width_be_b-1:0] byteena_b;
wire [(width_a-1):0] q_a_wire;
wire [(width_b-1):0] q_b_wire;
reg  clk_wire;


altsyncram altsyncram_component (
  .clock0 (clk_wire),
  .clock1 (1'd1),
  .clocken0 (clken),
  .clocken1 (1'd1),
  .clocken2 (1'd1),
  .clocken3 (1'd1),
  .aclr0 (1'd0),
  .aclr1 (1'd0),
  .addressstall_a (1'd0),
  .addressstall_b (1'd0),
  .eccstatus (),
  .address_a (address_a),
  .address_b (address_b),
  .rden_a (clken),
  .rden_b (clken),
  .q_a (q_a_wire),
  .q_b (q_b_wire),
  .byteena_a (byteena_a),
  .byteena_b (byteena_b),
  .wren_a (wren_a),
  .wren_b (wren_b),
  .data_a (data_a),
  .data_b (data_b)
);

defparam
  altsyncram_component.width_byteena_a = width_be_a,
  altsyncram_component.width_byteena_b = width_be_b,
  altsyncram_component.operation_mode = "BIDIR_DUAL_PORT",
  altsyncram_component.read_during_write_mode_mixed_ports = "OLD_DATA",
  altsyncram_component.init_file = init_file,
  altsyncram_component.lpm_hint = "ENABLE_RUNTIME_MOD=NO",
  altsyncram_component.lpm_type = "altsyncram",
  altsyncram_component.power_up_uninitialized = "FALSE",
  altsyncram_component.intended_device_family = "Cyclone V",
  altsyncram_component.clock_enable_input_a = "BYPASS",
  altsyncram_component.clock_enable_input_b = "BYPASS",
  altsyncram_component.clock_enable_output_a = "BYPASS",
  altsyncram_component.clock_enable_output_b = "BYPASS",
  altsyncram_component.outdata_aclr_a = "NONE",
  altsyncram_component.outdata_aclr_b = "NONE",
  altsyncram_component.outdata_reg_a = "UNREGISTERED",
  altsyncram_component.outdata_reg_b = "UNREGISTERED",
  altsyncram_component.numwords_a = numwords_a,
  altsyncram_component.numwords_b = numwords_b,
  altsyncram_component.widthad_a = widthad_a,
  altsyncram_component.widthad_b = widthad_b,
  altsyncram_component.width_a = width_a,
  altsyncram_component.width_b = width_b,
  altsyncram_component.address_reg_b = "CLOCK0",
  altsyncram_component.byteena_reg_b = "CLOCK0",
  altsyncram_component.indata_reg_b = "CLOCK0",
  altsyncram_component.wrcontrol_wraddress_reg_b = "CLOCK0";


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