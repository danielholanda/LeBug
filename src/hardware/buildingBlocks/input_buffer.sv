 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Circular queue of vectors for up to IB_DEPTH cycles
 //-----------------------------------------------------
`include "ram_dual_port.sv"

 module  inputBuffer #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter IB_DEPTH=4
  )
  (
  input logic clk,
  input logic enqueue,
  input logic eof_in,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg valid_out,
  output reg eof_out,
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0]
 );

    //----------Internal Variables------------
    reg [(DATA_WIDTH*N)-1:0] mem_array [IB_DEPTH-1 : 0];
    reg mem_array_valid [IB_DEPTH-1 : 0];
    reg [7:0] head = 8'b0;
    reg [7:0] tail = 8'b0;
    reg dequeue=1'b1; // THIS SHOULD BECOME AN INPUT LATER

    parameter latency = 2;
    parameter ram_latency = latency-1;

    //-------------Code Start-----------------


    always @(posedge clk) begin
      // Store valid inputs in buffer 
        if (enqueue==1'b1) begin
            mem_array[head]<= { << { vector_in }};
            mem_array_valid[head] <= enqueue;
            head <= head+1;
        end

        // Output values when "dequeue" is high
        if (dequeue==1'b1) begin
            valid_out <= { >> { mem_array_valid[tail] }};
            tail <= tail+1;
        end
    end

    assign eof_out = eof_in;
    assign vector_out = vector_in;


    reg [3:0] temp0_address_a;
    reg [3:0] temp0_address_b;
    reg temp0_write_enable_a;
    reg temp0_write_enable_b;
    reg [31:0] temp0_in_a;
    reg [31:0] temp0_in_b;
    wire [31:0] temp0_out_a;
    wire [31:0] temp0_out_b;

    // @temp0 = internal unnamed_addr global [1 x [10 x float]] zeroinitializer, align 8
    ram_dual_port temp0 (
      .clk( clk ),
      .clken( !memory_controller_waitrequest ),
      .address_a( temp0_address_a ),
      .address_b( temp0_address_b ),
      .wren_a( temp0_write_enable_a ),
      .wren_b( temp0_write_enable_b ),
      .data_a( temp0_in_a ),
      .data_b( temp0_in_b ),
      .byteena_a( 1'b1 ),
      .byteena_b( 1'b1 ),
      .q_a( temp0_out_a ),
      .q_b( temp0_out_b)
    );
    defparam temp0.width_a = 32;
    defparam temp0.width_b = 32;
    defparam temp0.widthad_a = 4;
    defparam temp0.widthad_b = 4;
    defparam temp0.width_be_a = 1;
    defparam temp0.width_be_b = 1;
    defparam temp0.numwords_a = 10;
    defparam temp0.numwords_b = 10;
    defparam temp0.latency = ram_latency;
    defparam temp0.init_file = "temp0.mif";

 
 endmodule 