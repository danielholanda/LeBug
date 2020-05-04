 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Buffers vectors for up to D cycles
 //-----------------------------------------------------
 module  input_buffer (
 input  wire  din_0      , // Mux first input
 input  wire  din_1      , // Mux Second input
 input  wire  sel        , // Select input
 output wire  mux_out      // Mux output
 );
 //-------------Code Start-----------------
 
     assign mux_out = (sel) ? din_1 : din_0;
 
 endmodule //End Of Module mux