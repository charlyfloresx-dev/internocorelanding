using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;

namespace Interno.HumanResource.Models.Catalog
{
    public class Contract
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength (10)]
        public string Code { get; set; }
        [MaxLength (250)]
        public string Description { get; set; }
        public int Days { get; set; }
        [Required]
        public bool Active { get; set; }   
    }
}