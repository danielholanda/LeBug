 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Circular queue of vectors for up to IB_DEPTH cycles
 //-----------------------------------------------------
`include "ram_dual_port.sv"

 module  inputBuffer #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter IB_DEPTH=4,
  parameter MAX_CHAINS=4,
  parameter INITIAL_FIRMWARE=0
  )
  (
  input logic clk,
  input logic enqueue,
  input logic eof_in,
  input logic tracing,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg valid_out,
  output reg eof_out,
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg [$clog2(MAX_CHAINS)-1:0] chainId_out=0
 );

    //----------Internal Variables------------
    reg dequeue=1'b1; 
    wire empty,full;
    reg valid_out_delay = 1'b0;
    reg [7:0] valid_chains = INITIAL_FIRMWARE;

    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = N*DATA_WIDTH;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(IB_DEPTH)-1:0] mem_address_a=1;
    reg [$clog2(IB_DEPTH)-1:0] mem_address_b=0;
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
      .address_b( mem_address_b ),
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
    defparam mem.widthad_a = $clog2(IB_DEPTH);
    defparam mem.widthad_b = $clog2(IB_DEPTH);
    defparam mem.width_be_a = 1;
    defparam mem.width_be_b = 1;
    defparam mem.numwords_a = IB_DEPTH;
    defparam mem.numwords_b = IB_DEPTH;
    defparam mem.latency = RAM_LATENCY;
    defparam mem.init_file = "inputBuffer.mif";

    always @(posedge clk) begin

        // Logic for enqueuing values
        if (enqueue==1'b1 & full==1'b0) begin
            mem_address_a <= mem_address_a<IB_DEPTH-1 ? mem_address_a+1'b1 : 0;
        end

        //Logic for dequeuing
        if (dequeue==1'b1 & empty==1'b0) begin
            mem_address_b <= mem_address_b<IB_DEPTH-1 ? mem_address_b+1'b1 : 0;
            valid_out_delay <= 1'b1;
        end
        else begin
            valid_out_delay <= 1'b0;
        end

        // 1-bit wide EOF signal is implemented as a bit shifter
        // FIXME - This is wrong -> We also need to create a memory/buffer for this
        eof_out <= eof_in;

        valid_out <= valid_out_delay;

        // loop over the different valid chains
        if (chainId_out<valid_chains-1 & valid_chains!=0) begin
          chainId_out<=chainId_out+1;
        end
        else begin
          chainId_out<=0;
        end
    end

    // Directly assign module inputs to port A of memory
    assign mem_in_a = { >> { vector_in }};
    assign mem_write_enable_a = enqueue;

    // Module output is the output of the queue
    assign vector_out = { >> { mem_out_b }};

    // Check if queue is empty/full
    assign empty = (mem_address_a-mem_address_b==1) | (mem_address_a==0 & mem_address_b==IB_DEPTH-1);
    assign full = (mem_address_a==mem_address_b);

 
 endmodule 