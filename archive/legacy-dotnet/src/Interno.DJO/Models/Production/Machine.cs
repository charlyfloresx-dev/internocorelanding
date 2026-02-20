using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Collections.Generic;

namespace Interno.DJO.Models.Production
{
    public class Machine
    {
        [Key]
        public string Id { get; set; }
        public string Module { get; set; }
        public string BussinesUnit { get; set; }
        public string Type { get; set; }
    }

}