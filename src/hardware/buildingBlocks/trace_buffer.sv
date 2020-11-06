 //-----------------------------------------------------
 // Design Name : Trace Buffer
 // Function    : Circular trace buffer of depth TB_SIZE
 //-----------------------------------------------------
`include "ram_dual_port.sv"

 module  traceBuffer #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter TB_SIZE=64
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic [$clog2(TB_SIZE)-1:0] tb_mem_address,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0]
 );

    //----------Internal Variables------------
    wire empty,full;

    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = N*DATA_WIDTH;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(TB_SIZE)-1:0] mem_address_a=0;
    wire mem_write_enable_a;
    reg mem_write_enable_b=0;
    wire [MEM_WIDTH-1:0] mem_in_a;
    reg [MEM_WIDTH-1:0] mem_in_b=0;
    wire [MEM_WIDTH-1:0] mem_out_a;
    wire [MEM_WIDTH-1:0] mem_out_b;
    ram_dual_port mem (
      .clk( clk ),
      .clken( 1'b1 ),
      .address_a( mem_address_a ),
      .address_b( tb_mem_address ),
      .wren_a( mem_write_enable_a ),
      .wren_b( mem_write_enable_b ),
      .data_a( mem_in_a ),
      .data_b( mem_in_b ),
      .byteena_a( 1'b1 ),
      .byteena_b( 1'b1 ),
      .q_a( mem_out_a ),
      .q_b( mem_out_b)
    );
    defparam mem.width_a = MEM_WIDTH;
    defparam mem.width_b = MEM_WIDTH;
    defparam mem.widthad_a = $clog2(TB_SIZE);
    defparam mem.widthad_b = $clog2(TB_SIZE);
    defparam mem.width_be_a = 1;
    defparam mem.width_be_b = 1;
    defparam mem.numwords_a = TB_SIZE;
    defparam mem.numwords_b = TB_SIZE;
    defparam mem.latency = RAM_LATENCY;
    defparam mem.init_file = "traceBuffer.mif";

    always @(posedge clk) begin

        // Logic for enqueuing values
        if (tracing==1'b1 & valid_in==1'b1) begin
            mem_address_a <= mem_address_a<TB_SIZE-1 ? mem_address_a+1'b1 : 0;
        end
    end


    // Directly assign module inputs to port A of memory
    assign mem_in_a = { >> { vector_in }};
    assign mem_write_enable_a = valid_in;

    // Module output comes from port b (need to drive it when dumping the content)
    assign vector_out = { >> { mem_out_b }};
 
 endmodule 